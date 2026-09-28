from fastapi import Request

from app.core.config import settings
from app.core.errors import AppError


def require_user_id(request: Request) -> str:
    user_id = request.session.get("user_id")
    if not isinstance(user_id, str) or not user_id:
        raise AppError(401, "authentication_required", "Sign in with GitHub to continue.")
    return user_id


def require_same_origin(request: Request) -> None:
    origin = request.headers.get("origin")
    if origin and origin.rstrip("/") != settings.frontend_origin.rstrip("/"):
        raise AppError(403, "origin_not_allowed", "This request origin is not allowed.")
