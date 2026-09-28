from fastapi import HTTPException


class AppError(HTTPException):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(status_code=status_code, detail={"code": code, "message": message})


def safe_upstream_error() -> AppError:
    return AppError(502, "upstream_unavailable", "A connected service is temporarily unavailable.")
