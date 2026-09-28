import json
import time
from collections.abc import AsyncIterator

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.api.dependencies import require_same_origin, require_user_id
from app.api.reviews import _active_reviews, _prune_expired
from app.core.errors import AppError
from app.services.chat_service import build_chat_prompt
from app.services.llm_client import GoogleAIClient

router = APIRouter(prefix="/api/reviews", tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=5000)


def _sse(event: dict[str, object]) -> str:
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


@router.post("/{review_id}/chat")
async def chat(review_id: str, payload: ChatRequest, request: Request) -> StreamingResponse:
    require_same_origin(request)
    user_id = require_user_id(request)
    _prune_expired()
    record = _active_reviews.get(review_id)
    if record is None or record["user_id"] != user_id:
        raise AppError(
            404, "review_not_found", "This review is no longer available in the active session."
        )
    record["last_access"] = time.monotonic()
    history = record["messages"]
    prompt = build_chat_prompt(record, payload.message)

    async def events() -> AsyncIterator[str]:
        parts: list[str] = []
        try:
            async for token in GoogleAIClient().stream(prompt):
                parts.append(token)
                yield _sse({"type": "token", "text": token})
            answer = "".join(parts)
            if answer:
                history.append({"role": "user", "content": payload.message})
                history.append({"role": "assistant", "content": answer})
                del history[:-40]
            record["last_access"] = time.monotonic()
            yield _sse({"type": "done"})
        except AppError as exc:
            yield _sse(
                {"type": "error", "message": exc.detail.get("message", "The chat service failed.")}
            )
        except Exception:
            yield _sse(
                {"type": "error", "message": "The chat response was interrupted. Please retry."}
            )

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no"},
    )
