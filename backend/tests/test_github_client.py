import httpx
import pytest

from app.core.config import settings
from app.core.errors import AppError
from app.services import github_client
from app.services.github_client import _get_with_retry, fetch_pull_request


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "url",
    [
        "http://github.com/owner/repo/pull/1",
        "https://github.com.evil.invalid/owner/repo/pull/1",
        "https://evil.invalid@github.com.evil.invalid/owner/repo/pull/1",
        "https://gitlab.com/owner/repo/merge_requests/1",
        "https://github.com/owner/repo/issues/1",
        "https://user:password@github.com/owner/repo/pull/1",
    ],
)
async def test_rejects_noncanonical_pull_request_urls_before_network(url):
    with pytest.raises(AppError) as exc:
        await fetch_pull_request(url, "unused-test-token")
    assert exc.value.status_code == 422
    assert exc.value.detail["code"] == "invalid_pr_url"


@pytest.mark.asyncio
async def test_github_rate_limit_uses_bounded_retry(monkeypatch):
    class Response:
        def __init__(self, status_code: int, headers: dict[str, str] | None = None):
            self.status_code = status_code
            self.headers = headers or {}
            self.is_error = status_code >= 400

    class Client:
        def __init__(self):
            self.responses = iter([Response(403, {"X-RateLimit-Remaining": "0"}), Response(200)])
            self.calls = 0

        async def get(self, _url: str, *, headers: dict[str, str]):
            self.calls += 1
            return next(self.responses)

    client = Client()
    monkeypatch.setattr(settings, "upstream_max_retries", 1)

    async def no_wait(_delay: float):
        return None

    monkeypatch.setattr("app.services.github_client.asyncio.sleep", no_wait)
    response = await _get_with_retry(client, "https://api.github.com/example", {})
    assert response.status_code == 200
    assert client.calls == 2


@pytest.mark.asyncio
async def test_fetch_pull_request_loads_metadata_diff_and_files(monkeypatch):
    seen: list[tuple[str, dict[str, str]]] = []

    class Response:
        status_code = 200
        is_error = False
        headers: dict[str, str] = {}

        def __init__(self, accept: str):
            self.accept = accept
            self.text = "diff --git a/src/a.py b/src/a.py\n"

        def json(self):
            if "application/vnd.github.diff" in self.accept:
                return {}
            if "/files?" in seen[-1][0]:
                return [{"filename": "src/a.py"}]
            return {"title": "Fix issue", "html_url": "https://github.com/acme/app/pull/42"}

    class Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def get(self, url: str, *, headers: dict[str, str]):
            seen.append((url, headers))
            return Response(headers.get("Accept", ""))

    monkeypatch.setattr(github_client.httpx, "AsyncClient", lambda **_kwargs: Client())
    metadata, diff, files = await fetch_pull_request(
        "https://github.com/acme/app/pull/42", "test-github-token"
    )
    assert metadata["title"] == "Fix issue"
    assert "diff --git" in diff
    assert files == [{"filename": "src/a.py"}]
    assert all(headers["Authorization"] == "Bearer test-github-token" for _, headers in seen)


@pytest.mark.asyncio
async def test_github_timeout_is_retried(monkeypatch):
    class Client:
        calls = 0

        async def get(self, _url: str, *, headers: dict[str, str]):
            self.calls += 1
            if self.calls == 1:
                raise httpx.ReadTimeout("test timeout")
            return type("Response", (), {"status_code": 200, "is_error": False, "headers": {}})()

    client = Client()
    monkeypatch.setattr(settings, "upstream_max_retries", 1)

    async def no_wait(_delay: float):
        return None

    monkeypatch.setattr("app.services.github_client.asyncio.sleep", no_wait)
    response = await _get_with_retry(client, "https://api.github.com/example", {})
    assert response.status_code == 200
    assert client.calls == 2
