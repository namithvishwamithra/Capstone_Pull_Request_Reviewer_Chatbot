import asyncio

import pytest
from fastapi import Request
from fastapi.testclient import TestClient

from app.api.reviews import _active_reviews, clear_user_reviews, export_review
from app.core.config import settings, validate_runtime_settings
from app.core.errors import AppError
from app.db.database import connect, init_db
from app.main import app
from app.schemas.review import Finding, ReviewResult


def test_health_and_cors_are_available(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path / 'test.db'}")
    with TestClient(app) as client:
        assert client.get("/api/health").json() == {"status": "ok"}
        allowed = client.options(
            "/api/reviews",
            headers={"Origin": settings.frontend_origin, "Access-Control-Request-Method": "POST"},
        )
        assert allowed.status_code == 200
        assert allowed.headers["access-control-allow-origin"] == settings.frontend_origin


def test_sqlite_schema_is_account_scoped(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path / 'test.db'}")
    init_db()
    with connect() as connection:
        connection.execute(
            "INSERT INTO users (id, github_id, login, encrypted_access_token) VALUES (?, ?, ?, ?)",
            ("u1", 1, "alice", b"encrypted"),
        )
        connection.execute(
            "INSERT INTO users (id, github_id, login, encrypted_access_token) VALUES (?, ?, ?, ?)",
            ("u2", 2, "bob", b"encrypted"),
        )
        connection.execute(
            "INSERT INTO daily_usage (user_id, usage_date) VALUES (?, ?)", ("u1", "2026-09-28")
        )
        assert connection.execute("SELECT count(*) FROM users").fetchone()[0] == 2
        assert (
            connection.execute("SELECT count(*) FROM daily_usage WHERE user_id='u2'").fetchone()[0]
            == 0
        )
        tables = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        assert {"saved_reviews", "saved_chat_messages"} <= tables
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 1


def test_oauth_callback_rejects_invalid_state_without_credentials():
    with TestClient(app) as client:
        response = client.get("/api/auth/callback?code=abc&state=forged", follow_redirects=False)
    assert response.status_code == 400


def test_production_startup_rejects_missing_required_secrets(monkeypatch):
    monkeypatch.setattr(settings, "production", True)
    monkeypatch.setattr(settings, "github_client_id", "")
    with pytest.raises(RuntimeError, match="GITHUB_CLIENT_ID"):
        validate_runtime_settings()


def test_validation_errors_do_not_echo_submitted_private_input():
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post(
            "/api/reviews",
            json={"diff": "private-source-secret", "consent_to_ai_processing": "not-a-boolean"},
        )
    assert response.status_code == 422
    assert "private-source-secret" not in response.text
    assert response.json()["detail"]["code"] == "invalid_request"


def test_ending_one_users_active_reviews_preserves_other_users_data():
    _active_reviews.clear()
    _active_reviews.update(
        {
            "review-one": {"user_id": "user-one"},
            "review-two": {"user_id": "user-two"},
        }
    )
    clear_user_reviews("user-one")
    assert set(_active_reviews) == {"review-two"}
    _active_reviews.clear()


def test_active_review_markdown_export_is_owner_scoped_and_escapes_markup():
    result = ReviewResult(
        id="review-markdown",
        title="Unsafe <img src=x>",
        summary="Summary with <script>alert(1)</script>.",
        findings=[
            Finding(
                severity="major",
                category="security",
                file="src/[auth].py",
                line_start=3,
                line_end=3,
                title="Dangerous **markup**",
                explanation="HTML <script> must render as text.",
                suggested_fix="Use a safe handler.",
            )
        ],
        changed_files=["src/[auth].py"],
        processed_changed_lines=1,
    )
    _active_reviews["review-markdown"] = {
        "user_id": "owner",
        "result": result,
        "last_access": 1e20,
    }
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/reviews/review-markdown/export",
            "headers": [(b"origin", settings.frontend_origin.encode())],
            "session": {"user_id": "owner"},
            "query_string": b"",
            "server": ("testserver", 80),
            "scheme": "http",
            "client": ("testclient", 50000),
        }
    )
    response = asyncio.run(export_review("review-markdown", request))
    assert response.status_code == 200
    assert "&lt;script&gt;" in response.body.decode()
    assert "\\*\\*markup\\*\\*" in response.body.decode()

    request.scope["session"]["user_id"] = "different-user"
    with pytest.raises(AppError) as exc:
        asyncio.run(export_review("review-markdown", request))
    assert exc.value.status_code == 404
    _active_reviews.clear()
