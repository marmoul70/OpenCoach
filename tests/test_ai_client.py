"""Tests du client Ollama sans serveur réel."""

import httpx
import pytest

from opencoach.ai.client import AIProviderError, OllamaClient
from opencoach.ai.config import AISettings
from opencoach.ai.schemas import AIChatRequest, AIMessage


def make_request():
    return AIChatRequest(
        messages=[AIMessage(role="user", content="Explique ma charge.")],
    )


@pytest.mark.asyncio
async def test_chat_sends_expected_payload_and_parses_response():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/chat"
        payload = __import__("json").loads(request.content)
        assert payload["model"] == "test-model"
        assert payload["stream"] is False
        assert payload["messages"][0]["content"] == "Explique ma charge."
        return httpx.Response(
            200,
            json={
                "model": "test-model",
                "message": {"role": "assistant", "content": "Analyse disponible."},
                "done": True,
            },
        )

    settings = AISettings(enabled=True, model="test-model")
    client = OllamaClient(settings, transport=httpx.MockTransport(handler))

    result = await client.chat(make_request())

    assert result.content == "Analyse disponible."
    assert result.model == "test-model"
    assert result.done is True


@pytest.mark.asyncio
async def test_http_error_is_sanitized():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, request=request)

    client = OllamaClient(
        AISettings(enabled=True),
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(AIProviderError, match="HTTP 503"):
        await client.chat(make_request())


@pytest.mark.asyncio
async def test_invalid_response_is_rejected():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"unexpected": True})

    client = OllamaClient(
        AISettings(enabled=True),
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(AIProviderError, match="ne respecte pas le contrat"):
        await client.chat(make_request())
