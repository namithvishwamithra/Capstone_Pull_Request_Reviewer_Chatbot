import re
import time
import uuid
from html import escape as escape_html

from cryptography.fernet import Fernet, InvalidToken
from fastapi import APIRouter, Request
from fastapi.responses import Response

from app.api.dependencies import require_same_origin, require_user_id
from app.core.config import settings
from app.core.errors import AppError
from app.db.database import connect
from app.schemas.review import ReviewRequest, ReviewResult
from app.services.github_client import fetch_pull_request
from app.services.review_input_service import consume_daily_limit, normalize_diff
from app.services.review_service import review_diff

router = APIRouter(prefix="/api/reviews", tags=["reviews"])

# Reviews contain submitted source code, so keep them only in process memory and expire them
# after 30 minutes of inactivity. They are never written to SQLite or logs.
_active_reviews: dict[str, dict[str, object]] = {}
SESSION_IDLE_SECONDS = 30 * 60


def _get_token(user_id: str) -> str:
    if not settings.token_encryption_key:
        raise AppError(
            503, "auth_not_configured", "GitHub sign-in is not configured on this server."
        )
    try:
        fernet = Fernet(settings.token_encryption_key.encode())
    except (ValueError, TypeError) as exc:
        raise AppError(
            503, "auth_not_configured", "GitHub sign-in is not configured on this server."
        ) from exc
    with connect() as connection:
        row = connection.execute(
            "SELECT encrypted_access_token FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    if row is None:
        raise AppError(401, "authentication_required", "Sign in with GitHub to continue.")
    try:
        return fernet.decrypt(row["encrypted_access_token"]).decode()
    except (InvalidToken, ValueError) as exc:
        raise AppError(
            503,
            "credential_unavailable",
            "GitHub access is unavailable. Please reconnect your account.",
        ) from exc


def _prune_expired() -> None:
    now = time.monotonic()
    for key in [
        key
        for key, value in _active_reviews.items()
        if float(value["last_access"]) + SESSION_IDLE_SECONDS < now
    ]:
        _active_reviews.pop(key, None)


def clear_user_reviews(user_id: str) -> None:
    for key in [key for key, value in _active_reviews.items() if value["user_id"] == user_id]:
        _active_reviews.pop(key, None)


@router.post("")
async def create_review(payload: ReviewRequest, request: Request) -> ReviewResult:
    require_same_origin(request)
    user_id = require_user_id(request)
    _prune_expired()
    token = _get_token(user_id)

    if payload.pr_url:
        metadata, diff, _ = await fetch_pull_request(payload.pr_url, token)
        title = str(metadata.get("title") or "GitHub pull request")
        description = str(metadata.get("body") or "")
        repository = metadata.get("html_url")
        if not isinstance(repository, str):
            repository = payload.pr_url
    else:
        diff = payload.diff or ""
        title, description, repository = "Pasted unified diff", "", None

    diff = normalize_diff(diff)
    consume_daily_limit(user_id)
    summary, findings, files, excluded, line_count = await review_diff(diff, title, description)
    review_id = str(uuid.uuid4())
    result = ReviewResult(
        id=review_id,
        title=title,
        summary=summary,
        findings=findings,
        changed_files=[file.path for file in files],
        excluded_files=excluded,
        processed_changed_lines=line_count,
        diff=diff,
    )
    _active_reviews[review_id] = {
        "user_id": user_id,
        "result": result,
        "diff": diff,
        "messages": [],
        "repository": repository,
        "last_access": time.monotonic(),
    }
    return result


@router.get("/{review_id}")
async def get_review(review_id: str, request: Request) -> dict[str, object]:
    user_id = require_user_id(request)
    _prune_expired()
    record = _active_reviews.get(review_id)
    if record is None or record["user_id"] != user_id:
        raise AppError(
            404, "review_not_found", "This review is no longer available in the active session."
        )
    record["last_access"] = time.monotonic()
    result = record["result"]
    return {**result.model_dump(mode="json"), "diff": record["diff"]}


@router.delete("/active")
async def end_active_session(request: Request) -> dict[str, bool]:
    user_id = require_user_id(request)
    require_same_origin(request)
    clear_user_reviews(user_id)
    return {"ok": True}


@router.post("/{review_id}/export")
async def export_review(review_id: str, request: Request) -> Response:
    user_id = require_user_id(request)
    require_same_origin(request)
    _prune_expired()
    record = _active_reviews.get(review_id)
    if record is None or record["user_id"] != user_id:
        raise AppError(
            404, "review_not_found", "This review is no longer available in the active session."
        )
    result = record["result"]

    def safe_markdown(value: str) -> str:
        escaped = escape_html(value, quote=False)
        return re.sub(r"([\\`*_{}\[\]()#+.!|>])", r"\\\1", escaped)

    lines = [
        f"# {safe_markdown(result.title)}",
        "",
        safe_markdown(result.summary),
        "",
        "## Findings",
        "",
    ]
    if not result.findings:
        lines.append("No actionable findings were identified.")
    for finding in result.findings:
        lines.extend(
            [
                f"### [{finding.severity.upper()}] {safe_markdown(finding.title)}",
                "",
                f"**{finding.category}** · `{safe_markdown(finding.file)}:{finding.line_start}-{finding.line_end}`",
                "",
                safe_markdown(finding.explanation),
                "",
            ]
        )
        if finding.suggested_fix:
            lines.extend([f"**Suggested fix:** {safe_markdown(finding.suggested_fix)}", ""])
    return Response(
        "\n".join(lines),
        media_type="text/markdown",
        headers={"Content-Disposition": 'attachment; filename="pull-request-review.md"'},
    )
