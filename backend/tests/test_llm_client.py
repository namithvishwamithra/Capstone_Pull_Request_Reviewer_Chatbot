import pytest

from app.core.config import settings
from app.services.llm_client import AnthropicAIClient, GoogleAIClient


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    @property
    def is_error(self):
        return self.status_code >= 400

    def json(self):
        return self._payload


class FakeClient:
    def __init__(self, response):
        self.response = response
        self.request = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        return None

    async def post(self, url, *, headers, json):
        self.request = (url, headers, json)
        return self.response

    def stream(self, method, url, *, headers, json):
        self.request = (url, headers, json)
        return self.response


class FakeStreamResponse(FakeResponse):
    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        return None

    async def aiter_lines(self):
        for line in (
            'data: {"type":"content_block_delta","delta":{"text":"Hello"}}',
            'data: {"type":"message_stop"}',
        ):
            yield line


@pytest.mark.asyncio
async def test_anthropic_generate_reads_message_content(monkeypatch):
    fake_client = FakeClient(FakeResponse({"content": [{"type": "text", "text": '{"ok":true}'}]}))
    monkeypatch.setattr("app.services.llm_client.httpx.AsyncClient", lambda **_: fake_client)
    monkeypatch.setattr(settings, "anthropic_api_key", "test-anthropic-key")

    result = await AnthropicAIClient().generate("review", json_mode=True)

    assert result == '{"ok":true}'
    assert fake_client.request[0] == "https://api.anthropic.com/v1/messages"
    assert fake_client.request[1]["anthropic-version"] == "2023-06-01"
    assert fake_client.request[2]["model"] == settings.anthropic_model


@pytest.mark.asyncio
async def test_anthropic_stream_reads_content_block_deltas(monkeypatch):
    fake_response = FakeStreamResponse({})
    fake_client = FakeClient(fake_response)
    monkeypatch.setattr("app.services.llm_client.httpx.AsyncClient", lambda **_: fake_client)
    monkeypatch.setattr(settings, "anthropic_api_key", "test-anthropic-key")
    monkeypatch.setattr(settings, "ai_provider", "anthropic")

    tokens = [token async for token in GoogleAIClient().stream("question")]

    assert tokens == ["Hello"]
