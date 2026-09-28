import secrets
import warnings
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware

from app.api import auth, chat, health, reviews
from app.core.config import settings, validate_runtime_settings
from app.db.database import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    validate_runtime_settings()
    init_db()
    if not settings.session_secret_key:
        warnings.warn(
            "SESSION_SECRET_KEY is unset; browser sessions will not survive process restarts. "
            "Set a persistent random value before deployment.",
            stacklevel=1,
        )
    yield


app = FastAPI(title="CAPSTONE Pull Request Reviewer API", version="0.1.0", lifespan=lifespan)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, __: RequestValidationError) -> JSONResponse:
    # Do not echo request inputs: they may contain private source code or user credentials.
    return JSONResponse(
        status_code=422,
        content={
            "detail": {
                "code": "invalid_request",
                "message": "Review input is invalid. Check the required fields and try again.",
            }
        },
    )


app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret_key or secrets.token_urlsafe(32),
    same_site="lax",
    https_only=settings.cookie_secure,
    session_cookie="capstone_session",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-Requested-With"],
)
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(reviews.router)
app.include_router(chat.router)
