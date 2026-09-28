import asyncio
import re

import httpx

from app.core.config import settings
from app.core.errors import AppError, safe_upstream_error

_PR_URL = re.compile(
    r"^https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)/pull/(\d+)(?:/.*)?$"
)


async def _get_with_retry(
    client: httpx.AsyncClient, url: str, headers: dict[str, str]
) -> httpx.Response:
    for attempt in range(settings.upstream_max_retries + 1):
        try:
            response = await client.get(url, headers=headers)
        except httpx.HTTPError as exc:
            if attempt >= settings.upstream_max_retries:
                raise safe_upstream_error() from exc
            await asyncio.sleep(min(0.25 * (2**attempt), 2.0))
            continue
        rate_limited = (
            response.status_code == 403 and response.headers.get("X-RateLimit-Remaining") == "0"
        )
        if response.status_code == 429 or response.status_code >= 500 or rate_limited:
            if attempt >= settings.upstream_max_retries:
                raise safe_upstream_error()
            await asyncio.sleep(min(0.25 * (2**attempt), 2.0))
            continue
        if response.status_code in (401, 403, 404):
            raise AppError(
                400,
                "pull_request_unavailable",
                "The pull request is private, missing, or inaccessible to this account.",
            )
        if response.is_error:
            raise AppError(
                400, "pull_request_invalid", "GitHub could not retrieve that pull request."
            )
        return response
    raise safe_upstream_error()


async def fetch_pull_request(
    pr_url: str, token: str
) -> tuple[dict[str, object], str, list[dict[str, object]]]:
    match = _PR_URL.fullmatch(pr_url.strip())
    if not match:
        raise AppError(
            422,
            "invalid_pr_url",
            "Enter a GitHub pull request URL such as https://github.com/owner/repo/pull/123.",
        )
    owner, repo, number = match.groups()
    api_base = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "capstone-pr-reviewer",
    }
    try:
        async with httpx.AsyncClient(
            timeout=settings.upstream_timeout_seconds, follow_redirects=False
        ) as client:
            metadata_response = await _get_with_retry(client, api_base, headers)
            metadata = metadata_response.json()
            diff_response = await _get_with_retry(
                client, api_base, {**headers, "Accept": "application/vnd.github.diff"}
            )
            diff = diff_response.text
            files_response = await _get_with_retry(
                client, f"{api_base}/files?per_page=100", headers
            )
            files = files_response.json()
    except AppError:
        raise
    except (ValueError, httpx.HTTPError) as exc:
        raise safe_upstream_error() from exc
    if not isinstance(metadata, dict) or not isinstance(files, list):
        raise AppError(
            502, "github_response_invalid", "GitHub returned an invalid pull request response."
        )
    return metadata, diff, files
