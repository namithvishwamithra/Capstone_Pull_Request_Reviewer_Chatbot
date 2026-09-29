import asyncio
import json

import httpx

from app.core.config import settings
from app.core.errors import AppError, safe_upstream_error


class GoogleAIClient:
    def __init__(self) -> None:
        self._client = (
            AnthropicAIClient() if settings.ai_provider == "anthropic" else _GoogleAIClient()
        )

    async def generate(
        self, prompt: str, *, temperature: float = 0.1, json_mode: bool = False
    ) -> str:
        return await self._client.generate(prompt, temperature=temperature, json_mode=json_mode)

    async def stream(self, prompt: str):
        async for token in self._client.stream(prompt):
            yield token


class _GoogleAIClient:
    def __init__(self) -> None:
        self._base_url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{settings.google_ai_model}"
        )

    def _require_key(self) -> str:
        if not settings.google_ai_studio_api_key:
            raise AppError(503, "ai_not_configured", "AI review is not configured on this server.")
        return settings.google_ai_studio_api_key

    async def generate(
        self, prompt: str, *, temperature: float = 0.1, json_mode: bool = False
    ) -> str:
        key = self._require_key()
        payload: dict[str, object] = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": temperature, "maxOutputTokens": 8192},
        }
        if json_mode:
            payload["generationConfig"]["responseMimeType"] = "application/json"  # type: ignore[index]
        for attempt in range(settings.upstream_max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=settings.upstream_timeout_seconds) as client:
                    response = await client.post(
                        f"{self._base_url}:generateContent",
                        headers={"x-goog-api-key": key},
                        json=payload,
                    )
                if response.status_code == 429 or response.status_code >= 500:
                    if attempt < settings.upstream_max_retries:
                        await asyncio.sleep(min(0.25 * (2**attempt), 2.0))
                        continue
                    raise safe_upstream_error()
                if response.is_error:
                    # Never surface provider response bodies or URLs, which can include sensitive data.
                    raise AppError(
                        502,
                        "ai_request_failed",
                        "The review service could not complete the request.",
                    )
                data = response.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                if not isinstance(text, str):
                    raise ValueError("Missing text")
                return text
            except AppError:
                raise
            except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError) as exc:
                if attempt < settings.upstream_max_retries and isinstance(exc, httpx.HTTPError):
                    await asyncio.sleep(min(0.25 * (2**attempt), 2.0))
                    continue
                raise safe_upstream_error() from exc
        raise safe_upstream_error()

    async def stream(self, prompt: str):
        key = self._require_key()
        url = f"{self._base_url}:streamGenerateContent"
        for attempt in range(settings.upstream_max_retries + 1):
            emitted_token = False
            try:
                async with httpx.AsyncClient(timeout=settings.upstream_timeout_seconds) as client:
                    async with client.stream(
                        "POST",
                        url,
                        params={"alt": "sse"},
                        headers={"x-goog-api-key": key},
                        json={
                            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                            "generationConfig": {"temperature": 0.4, "maxOutputTokens": 2048},
                        },
                    ) as response:
                        if response.status_code == 429 or response.status_code >= 500:
                            if attempt < settings.upstream_max_retries:
                                await asyncio.sleep(min(0.25 * (2**attempt), 2.0))
                                continue
                            raise safe_upstream_error()
                        if response.is_error:
                            raise safe_upstream_error()
                        async for line in response.aiter_lines():
                            if not line.startswith("data:"):
                                continue
                            value = line[5:].strip()
                            if not value or value == "[DONE]":
                                continue
                            try:
                                data = json.loads(value)
                                text = data["candidates"][0]["content"]["parts"][0].get("text", "")
                            except (ValueError, KeyError, IndexError, TypeError):
                                continue
                            if text:
                                emitted_token = True
                                yield text
                return
            except AppError:
                raise
            except httpx.HTTPError as exc:
                if attempt < settings.upstream_max_retries and not emitted_token:
                    await asyncio.sleep(min(0.25 * (2**attempt), 2.0))
                    continue
                raise safe_upstream_error() from exc
        raise safe_upstream_error()


class AnthropicAIClient:
    _base_url = "https://api.anthropic.com/v1/messages"

    def _require_key(self) -> str:
        if not settings.anthropic_api_key:
            raise AppError(503, "ai_not_configured", "AI review is not configured on this server.")
        return settings.anthropic_api_key

    def _headers(self, key: str) -> dict[str, str]:
        return {
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

    def _payload(self, prompt: str, temperature: float, max_tokens: int) -> dict[str, object]:
        return {
            "model": settings.anthropic_model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }

    async def generate(
        self, prompt: str, *, temperature: float = 0.1, json_mode: bool = False
    ) -> str:
        del json_mode
        key = self._require_key()
        for attempt in range(settings.upstream_max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=settings.upstream_timeout_seconds) as client:
                    response = await client.post(
                        self._base_url,
                        headers=self._headers(key),
                        json=self._payload(prompt, temperature, 8192),
                    )
                if response.status_code == 429 or response.status_code >= 500:
                    if attempt < settings.upstream_max_retries:
                        await asyncio.sleep(min(0.25 * (2**attempt), 2.0))
                        continue
                    raise safe_upstream_error()
                if response.is_error:
                    raise AppError(
                        502,
                        "ai_request_failed",
                        "The review service could not complete the request.",
                    )
                data = response.json()
                blocks = data["content"]
                text = "".join(
                    block.get("text", "")
                    for block in blocks
                    if isinstance(block, dict) and block.get("type") == "text"
                )
                if not text:
                    raise ValueError("Missing text")
                return text
            except AppError:
                raise
            except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
                if attempt < settings.upstream_max_retries and isinstance(exc, httpx.HTTPError):
                    await asyncio.sleep(min(0.25 * (2**attempt), 2.0))
                    continue
                raise safe_upstream_error() from exc
        raise safe_upstream_error()

    async def stream(self, prompt: str):
        key = self._require_key()
        payload = self._payload(prompt, 0.4, 2048)
        payload["stream"] = True
        for attempt in range(settings.upstream_max_retries + 1):
            emitted_token = False
            try:
                async with httpx.AsyncClient(timeout=settings.upstream_timeout_seconds) as client:
                    async with client.stream(
                        "POST", self._base_url, headers=self._headers(key), json=payload
                    ) as response:
                        if response.status_code == 429 or response.status_code >= 500:
                            if attempt < settings.upstream_max_retries:
                                await asyncio.sleep(min(0.25 * (2**attempt), 2.0))
                                continue
                            raise safe_upstream_error()
                        if response.is_error:
                            raise safe_upstream_error()
                        async for line in response.aiter_lines():
                            if not line.startswith("data:"):
                                continue
                            try:
                                event = json.loads(line[5:].strip())
                            except ValueError:
                                continue
                            if event.get("type") != "content_block_delta":
                                continue
                            text = event.get("delta", {}).get("text", "")
                            if text:
                                emitted_token = True
                                yield text
                return
            except AppError:
                raise
            except httpx.HTTPError as exc:
                if attempt < settings.upstream_max_retries and not emitted_token:
                    await asyncio.sleep(min(0.25 * (2**attempt), 2.0))
                    continue
                raise safe_upstream_error() from exc
        raise safe_upstream_error()
