import secrets
import uuid
from urllib.parse import urlencode

import httpx
from cryptography.fernet import Fernet
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from app.api.dependencies import require_same_origin
from app.core.config import settings
from app.core.errors import AppError, safe_upstream_error
from app.db.database import connect

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _fernet() -> Fernet:
    if not settings.token_encryption_key:
        raise AppError(
            503, "auth_not_configured", "GitHub sign-in is not configured on this server."
        )
    try:
        return Fernet(settings.token_encryption_key.encode())
    except (ValueError, TypeError) as exc:
        raise AppError(
            503, "auth_not_configured", "GitHub sign-in is not configured on this server."
        ) from exc


@router.get("/login")
async def login(request: Request) -> RedirectResponse:
    if not settings.github_client_id or not settings.github_client_secret:
        raise AppError(
            503, "auth_not_configured", "GitHub sign-in is not configured on this server."
        )
    state = secrets.token_urlsafe(32)
    request.session["oauth_state"] = state
    query = urlencode(
        {
            "client_id": settings.github_client_id,
            "redirect_uri": settings.github_redirect_uri,
            "scope": "read:user user:email",
            "state": state,
        }
    )
    return RedirectResponse(f"https://github.com/login/oauth/authorize?{query}", status_code=302)


@router.get("/callback")
async def callback(request: Request, code: str = "", state: str = "") -> RedirectResponse:
    expected_state = request.session.pop("oauth_state", "")
    if not code or not state or not secrets.compare_digest(str(expected_state), state):
        raise AppError(
            400, "oauth_state_invalid", "GitHub sign-in could not be verified. Please try again."
        )
    if not settings.github_client_id or not settings.github_client_secret:
        raise AppError(
            503, "auth_not_configured", "GitHub sign-in is not configured on this server."
        )

    headers = {"Accept": "application/json", "User-Agent": "capstone-pr-reviewer"}
    try:
        async with httpx.AsyncClient(timeout=settings.upstream_timeout_seconds) as client:
            token_response = await client.post(
                "https://github.com/login/oauth/access_token",
                data={
                    "client_id": settings.github_client_id,
                    "client_secret": settings.github_client_secret,
                    "code": code,
                    "redirect_uri": settings.github_redirect_uri,
                },
                headers=headers,
            )
            token_response.raise_for_status()
            token = token_response.json().get("access_token")
            if not isinstance(token, str) or not token:
                raise AppError(
                    502, "oauth_exchange_failed", "GitHub sign-in could not be completed."
                )
            user_response = await client.get(
                "https://api.github.com/user",
                headers={**headers, "Authorization": f"Bearer {token}"},
            )
            user_response.raise_for_status()
            profile = user_response.json()
    except AppError:
        raise
    except (httpx.HTTPError, ValueError) as exc:
        raise safe_upstream_error() from exc

    github_id = profile.get("id")
    login_name = profile.get("login")
    if not isinstance(github_id, int) or not isinstance(login_name, str):
        raise AppError(502, "oauth_profile_invalid", "GitHub returned an invalid account profile.")
    user_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"github:{github_id}"))
    encrypted_token = _fernet().encrypt(token.encode())
    with connect() as connection:
        connection.execute(
            """INSERT INTO users (id, github_id, login, display_name, avatar_url, encrypted_access_token)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(github_id) DO UPDATE SET login=excluded.login,
                 display_name=excluded.display_name, avatar_url=excluded.avatar_url,
                 encrypted_access_token=excluded.encrypted_access_token,
                 updated_at=CURRENT_TIMESTAMP""",
            (
                user_id,
                github_id,
                login_name,
                profile.get("name"),
                profile.get("avatar_url"),
                encrypted_token,
            ),
        )
        row = connection.execute(
            "SELECT id FROM users WHERE github_id = ?", (github_id,)
        ).fetchone()
    request.session.clear()
    request.session["user_id"] = row["id"]
    return RedirectResponse(settings.frontend_origin, status_code=303)


@router.get("/me")
async def me(request: Request) -> dict[str, object]:
    user_id = request.session.get("user_id")
    if not isinstance(user_id, str):
        return {"authenticated": False, "user": None}
    with connect() as connection:
        row = connection.execute(
            "SELECT id, login, display_name, avatar_url FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    if row is None:
        request.session.clear()
        return {"authenticated": False, "user": None}
    return {
        "authenticated": True,
        "user": {
            "id": row["id"],
            "login": row["login"],
            "display_name": row["display_name"],
            "avatar_url": row["avatar_url"],
        },
    }


@router.post("/logout")
async def logout(request: Request) -> dict[str, bool]:
    require_same_origin(request)
    user_id = request.session.get("user_id")
    if isinstance(user_id, str):
        from app.api.reviews import clear_user_reviews

        clear_user_reviews(user_id)
    request.session.clear()
    return {"ok": True}
