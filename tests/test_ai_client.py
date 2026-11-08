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
        assert "think" not in payload
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


def test_timeout_is_reported_without_transport_details():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("private transport detail", request=request)

    async def run():
        client = OllamaClient(
            AISettings(enabled=True),
            transport=httpx.MockTransport(handler),
        )
        await client.chat(make_request())

    with pytest.raises(AIProviderError, match="délai imparti") as error:
        asyncio.run(run())

    assert "private transport detail" not in str(error.value)


def test_connection_error_is_sanitized():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("private host detail", request=request)

    async def run():
        client = OllamaClient(
            AISettings(enabled=True),
            transport=httpx.MockTransport(handler),
        )
        await client.chat(make_request())

    with pytest.raises(AIProviderError, match="Impossible de communiquer") as error:
        asyncio.run(run())

    assert "private host detail" not in str(error.value)


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



def test_qwen3_disables_internal_thinking_to_preserve_answer_tokens():
    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert payload["model"] == "qwen3:8b"
        assert payload["think"] is False
        return httpx.Response(
            200,
            json={
                "model": "qwen3:8b",
                "message": {"role": "assistant", "content": "Analyse complète."},
                "done": True,
            },
        )

    async def run():
        settings = AISettings(enabled=True, model="qwen3:8b")
        client = OllamaClient(settings, transport=httpx.MockTransport(handler))
        return await client.chat(make_request())

    result = asyncio.run(run())
    assert result.content == "Analyse complète."
    assert result.done is True
