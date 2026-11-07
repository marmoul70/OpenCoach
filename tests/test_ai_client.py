"""Tests du client Ollama sans serveur réel."""

import asyncio
import json

import httpx
import pytest

from opencoach.ai.client import AIProviderError, OllamaClient
from opencoach.ai.config import AISettings
from opencoach.ai.schemas import AIChatRequest, AIMessage


def make_request():
    return AIChatRequest(
        messages=[AIMessage(role="user", content="Explique ma charge.")],
    )


def test_chat_sends_expected_payload_and_parses_response():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/chat"
        payload = json.loads(request.content)
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

    async def run():
        settings = AISettings(enabled=True, model="test-model")
        client = OllamaClient(settings, transport=httpx.MockTransport(handler))
        return await client.chat(make_request())

    result = asyncio.run(run())

    assert result.content == "Analyse disponible."
    assert result.model == "test-model"
    assert result.done is True


def test_http_error_is_sanitized():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, request=request)

    async def run():
        client = OllamaClient(
            AISettings(enabled=True),
            transport=httpx.MockTransport(handler),
        )
        await client.chat(make_request())

    with pytest.raises(AIProviderError, match="HTTP 503"):
        asyncio.run(run())


def test_invalid_response_is_rejected():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"unexpected": True})

    async def run():
        client = OllamaClient(
            AISettings(enabled=True),
            transport=httpx.MockTransport(handler),
        )
        await client.chat(make_request())

    with pytest.raises(AIProviderError, match="ne respecte pas le contrat"):
        asyncio.run(run())
