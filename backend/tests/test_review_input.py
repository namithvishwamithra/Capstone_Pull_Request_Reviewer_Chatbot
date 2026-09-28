import pytest
from pydantic import ValidationError

from app.core.config import settings
from app.core.errors import AppError
from app.db.database import connect, init_db
from app.schemas.review import ReviewRequest
from app.services.review_input_service import consume_daily_limit, normalize_diff


def test_review_request_requires_exactly_one_source_and_consent():
    with pytest.raises(ValidationError):
        ReviewRequest(consent_to_ai_processing=True)
    with pytest.raises(ValidationError):
        ReviewRequest(
            pr_url="https://github.com/a/b/pull/1", diff="x", consent_to_ai_processing=True
        )
    with pytest.raises(ValidationError):
        ReviewRequest(diff="diff", consent_to_ai_processing=False)


def test_diff_normalization_accepts_line_endings_and_rejects_empty_input():
    patch = "diff --git a/a.py b/a.py\r\n--- a/a.py\r\n+++ b/a.py\r\n@@ -0,0 +1 @@\r\n+value\r\n"
    assert "\r" not in normalize_diff(patch)
    with pytest.raises(AppError) as exc:
        normalize_diff("  \n\t")
    assert exc.value.detail["code"] == "empty_diff"


def test_review_size_cap_rejects_more_than_configured_lines():
    diff = "diff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py\n@@ -0,0 +1,1001 @@\n" + "".join(
        f"+line_{index}\n" for index in range(1001)
    )
    with pytest.raises(AppError) as exc:
        normalize_diff(diff)
    assert exc.value.status_code == 413
    assert exc.value.detail["code"] == "diff_too_large"


def test_daily_review_limit_is_scoped_per_account(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path / 'quota.db'}")
    monkeypatch.setattr(settings, "per_user_daily_review_limit", 1)
    init_db()
    with connect() as connection:
        for user_id, github_id in (("user-a", 1), ("user-b", 2)):
            connection.execute(
                "INSERT INTO users (id, github_id, login, encrypted_access_token) VALUES (?, ?, ?, ?)",
                (user_id, github_id, user_id, b"encrypted"),
            )
    consume_daily_limit("user-a")
    consume_daily_limit("user-b")
    with pytest.raises(AppError) as exc:
        consume_daily_limit("user-a")
    assert exc.value.status_code == 429
    assert exc.value.detail["code"] == "daily_limit_reached"
