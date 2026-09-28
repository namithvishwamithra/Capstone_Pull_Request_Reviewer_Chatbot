from datetime import UTC, datetime

from app.core.config import settings
from app.core.errors import AppError
from app.db.database import connect
from app.services.diff_parser import changed_line_count, parse_unified_diff


def normalize_diff(diff: str) -> str:
    normalized = diff.replace("\r\n", "\n").replace("\r", "\n")
    if not normalized.strip():
        raise AppError(422, "empty_diff", "Paste a non-empty unified diff to start a review.")
    line_count = changed_line_count(parse_unified_diff(normalized))
    if line_count > settings.max_changed_lines:
        raise AppError(
            413,
            "diff_too_large",
            f"This diff has more than {settings.max_changed_lines} changed lines. Reduce the diff size and try again.",
        )
    return normalized


def consume_daily_limit(user_id: str) -> None:
    today = datetime.now(UTC).date().isoformat()
    with connect() as connection:
        connection.execute(
            "INSERT INTO daily_usage (user_id, usage_date, review_count) VALUES (?, ?, 0) "
            "ON CONFLICT(user_id, usage_date) DO NOTHING",
            (user_id, today),
        )
        row = connection.execute(
            "SELECT review_count FROM daily_usage WHERE user_id = ? AND usage_date = ?",
            (user_id, today),
        ).fetchone()
        if row["review_count"] >= settings.per_user_daily_review_limit:
            raise AppError(
                429,
                "daily_limit_reached",
                "Your daily review limit has been reached. Try again tomorrow.",
            )
        connection.execute(
            "UPDATE daily_usage SET review_count = review_count + 1 "
            "WHERE user_id = ? AND usage_date = ?",
            (user_id, today),
        )
