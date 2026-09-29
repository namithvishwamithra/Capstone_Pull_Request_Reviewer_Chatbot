from functools import lru_cache
from typing import Literal
from urllib.parse import urlsplit

from cryptography.fernet import Fernet
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    github_client_id: str = ""
    github_client_secret: str = ""
    github_redirect_uri: str = "http://localhost:8000/api/auth/callback"
    session_secret_key: str = ""
    token_encryption_key: str = ""
    ai_provider: Literal["google", "anthropic"] = "google"
    google_ai_studio_api_key: str = ""
    google_ai_model: str = "gemma-4-26b-a4b-it"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    database_url: str = "sqlite:///./capstone.db"
    frontend_origin: str = "http://localhost:5173"
    backend_origin: str = "http://localhost:8000"
    cookie_secure: bool = False
    production: bool = False
    max_changed_lines: int = Field(default=1000, gt=0)
    per_user_daily_review_limit: int = Field(default=30, gt=0)
    upstream_timeout_seconds: float = Field(default=20.0, gt=0)
    upstream_max_retries: int = Field(default=3, ge=0, le=5)

    @field_validator("github_redirect_uri", "frontend_origin", "backend_origin")
    @classmethod
    def validate_http_origins(cls, value: str) -> str:
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("Origins must be absolute HTTP or HTTPS URLs.")
        return value.rstrip("/")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()


def validate_runtime_settings() -> None:
    """Fail closed for unsafe or incomplete production configuration."""
    if not settings.database_url.startswith("sqlite:///"):
        raise RuntimeError("Only a SQLite DATABASE_URL is supported by the initial release.")
    if not settings.production:
        return
    provider_key = (
        settings.google_ai_studio_api_key
        if settings.ai_provider == "google"
        else settings.anthropic_api_key
    )
    required = {
        "GITHUB_CLIENT_ID": settings.github_client_id,
        "GITHUB_CLIENT_SECRET": settings.github_client_secret,
        "SESSION_SECRET_KEY": settings.session_secret_key,
        "TOKEN_ENCRYPTION_KEY": settings.token_encryption_key,
        "AI_PROVIDER_API_KEY": provider_key,
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise RuntimeError(f"Missing required production settings: {', '.join(missing)}")
    if not settings.cookie_secure:
        raise RuntimeError("COOKIE_SECURE must be enabled in production.")
    if not settings.frontend_origin.startswith(
        "https://"
    ) or not settings.backend_origin.startswith("https://"):
        raise RuntimeError("Production frontend and backend origins must use HTTPS.")
    try:
        Fernet(settings.token_encryption_key.encode())
    except (ValueError, TypeError) as exc:
        raise RuntimeError("TOKEN_ENCRYPTION_KEY must be a valid Fernet key.") from exc
