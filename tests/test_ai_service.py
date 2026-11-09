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



def test_tool_orchestration_executes_validated_tool_then_returns_final_answer():
    from pydantic import BaseModel, ConfigDict
    from opencoach.ai.schemas import AIToolCall
    from opencoach.ai.tool_engine import AITool, AIToolRegistry

    class Args(BaseModel):
        model_config = ConfigDict(extra="forbid")
        nb_days: int

    class ToolCallingClient:
        def __init__(self):
            self.calls = 0
            self.requests = []

        async def chat(self, request):
            self.calls += 1
            self.requests.append(request)
            if self.calls == 1:
                return AIChatResult(
                    model="qwen3:8b",
                    content="",
                    tool_calls=[AIToolCall(name="history", arguments={"nb_days": 7})],
                    done=True,
                )
            return AIChatResult(
                model="qwen3:8b",
                content="Bilan sur 7 jours.",
                done=True,
            )

    registry = AIToolRegistry()
    registry.register(AITool(
        name="history",
        description="Historique.",
        arguments_model=Args,
        handler=lambda args: {"days": args.nb_days},
    ))
    client = ToolCallingClient()
    service = AIService(AISettings(enabled=True), client=client)
    request = AIChatRequest(messages=[AIMessage(role="user", content="Mon historique")])

    result = asyncio.run(service.chat_with_tools(request, registry))

    assert result.content == "Bilan sur 7 jours."
    assert client.calls == 2
    assert client.requests[0].tools[0].name == "history"
    assert client.requests[1].messages[-1].role == "tool"
    assert '"days": 7' in client.requests[1].messages[-1].content



def test_missing_required_tool_argument_is_returned_to_model_for_clarification():
    from opencoach.ai.schemas import AIToolCall
    from opencoach.ai.tool_engine import AITool, AIToolRegistry
    from opencoach.ai.training_tools import TrainingHistoryArguments

    class ClarifyingClient:
        def __init__(self):
            self.calls = 0
            self.follow_up_tool_message = None

        async def chat(self, request):
            self.calls += 1
            if self.calls == 1:
                return AIChatResult(
                    model="qwen3:8b",
                    content="",
                    tool_calls=[AIToolCall(name="training_history", arguments={})],
                    done=True,
                )
            self.follow_up_tool_message = request.messages[-1].content
            return AIChatResult(
                model="qwen3:8b",
                content="Sur combien de jours souhaites-tu ton historique ?",
                done=True,
            )

    registry = AIToolRegistry()
    registry.register(AITool(
        name="training_history",
        description="Historique sportif.",
        arguments_model=TrainingHistoryArguments,
        handler=lambda args: {"days": args.nb_days},
    ))
    client = ClarifyingClient()
    service = AIService(AISettings(enabled=True), client=client)
    request = AIChatRequest(messages=[
        AIMessage(role="user", content="Montre-moi mon historique.")
    ])

    result = asyncio.run(service.chat_with_tools(request, registry))

    assert result.content == "Sur combien de jours souhaites-tu ton historique ?"
    assert client.calls == 2
    assert "invalid_arguments" in client.follow_up_tool_message
    assert "paramètres" in client.follow_up_tool_message
