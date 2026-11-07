"""Tests de la façade IA et de son interrupteur de sécurité."""

import asyncio

import pytest

from opencoach.ai.config import AISettings
from opencoach.ai.schemas import AIChatRequest, AIChatResult, AIMessage
from opencoach.ai.service import AIService, AIServiceDisabledError


class FakeClient:
    def __init__(self):
        self.calls = 0

    async def chat(self, request):
        self.calls += 1
        return AIChatResult(
            model="fake",
            content="Réponse de test.",
            done=True,
        )


def test_disabled_service_never_calls_provider():
    client = FakeClient()
    service = AIService(
        AISettings(enabled=False),
        client=client,
    )
    request = AIChatRequest(
        messages=[AIMessage(role="user", content="Bonjour")],
    )

    async def run():
        with pytest.raises(AIServiceDisabledError):
            await service.chat(request)

    asyncio.run(run())
    assert client.calls == 0


def test_enabled_service_calls_provider():
    client = FakeClient()
    service = AIService(
        AISettings(enabled=True),
        client=client,
    )
    request = AIChatRequest(
        messages=[AIMessage(role="user", content="Bonjour")],
    )

    result = asyncio.run(service.chat(request))

    assert result.content == "Réponse de test."
    assert client.calls == 1
