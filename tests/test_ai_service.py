"""Tests de la façade IA et de son interrupteur de sécurité."""

import asyncio

import pytest
from pydantic import BaseModel

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


def test_tool_orchestration_stops_and_asks_for_period_when_model_invents_one():
    from pydantic import BaseModel, ConfigDict
    from opencoach.ai.schemas import AIToolCall
    from opencoach.ai.tool_engine import AITool, AIToolRegistry
    from opencoach.ai.argument_evidence import validate_period_argument_evidence

    class Args(BaseModel):
        model_config = ConfigDict(extra="forbid")
        nb_days: int

    class InventingClient:
        def __init__(self):
            self.calls = 0

        async def chat(self, request):
            self.calls += 1
            return AIChatResult(model="qwen3:8b", content="", tool_calls=[AIToolCall(name="training_history", arguments={"nb_days": 7})], done=True)

    executions = []
    registry = AIToolRegistry(argument_guard=validate_period_argument_evidence)
    registry.register(AITool(name="training_history", description="Historique.", arguments_model=Args, handler=lambda args: executions.append(args.nb_days) or {"days": args.nb_days}))
    client = InventingClient()
    service = AIService(AISettings(enabled=True), client=client)
    request = AIChatRequest(messages=[AIMessage(role="user", content="Fais-moi le bilan de mon historique.")])
    result = asyncio.run(service.chat_with_tools(request, registry, user_messages=["Fais-moi le bilan de mon historique."]))
    assert result.content == "Sur combien de jours souhaites-tu que j'analyse ton historique ?"
    assert client.calls == 1
    assert executions == []
    assert registry.execution_results[-1].status == "needs_clarification"


def test_tool_orchestration_rejects_period_not_matching_user_request():
    from pydantic import BaseModel, ConfigDict
    from opencoach.ai.schemas import AIToolCall
    from opencoach.ai.tool_engine import AITool, AIToolRegistry
    from opencoach.ai.argument_evidence import validate_period_argument_evidence

    class Args(BaseModel):
        model_config = ConfigDict(extra="forbid")
        nb_days: int

    class WrongPeriodClient:
        async def chat(self, request):
            return AIChatResult(model="qwen3:8b", content="", tool_calls=[AIToolCall(name="training_history", arguments={"nb_days": 30})], done=True)

    executions = []
    registry = AIToolRegistry(argument_guard=validate_period_argument_evidence)
    registry.register(AITool(name="training_history", description="Historique.", arguments_model=Args, handler=lambda args: executions.append(args.nb_days) or {"days": args.nb_days}))
    service = AIService(AISettings(enabled=True), client=WrongPeriodClient())
    request = AIChatRequest(messages=[AIMessage(role="user", content="Analyse mon historique sur 7 jours.")])
    result = asyncio.run(service.chat_with_tools(request, registry, user_messages=["Analyse mon historique sur 7 jours."]))
    assert "Tu as indiqué 7 jours" in result.content
    assert executions == []


def test_truncated_tool_call_is_rejected_before_business_handler_execution():
    from opencoach.ai.schemas import AIToolCall
    from opencoach.ai.service import AIOrchestrationError
    from opencoach.ai.tool_engine import AITool, AIToolRegistry

    executions = []

    class TruncatedToolCallingClient:
        async def chat(self, request):
            return AIChatResult(
                model="qwen2.5:3b",
                content="",
                tool_calls=[
                    AIToolCall(name="write_data", arguments={"value": 3})
                ],
                done=True,
                done_reason="length",
            )

    registry = AIToolRegistry()
    registry.register(AITool(
        name="write_data",
        description="Écriture de test.",
        arguments_model=EchoArgsForTruncationTest,
        handler=lambda args: executions.append(args.value) or {"saved": True},
    ))
    service = AIService(
        AISettings(enabled=True),
        client=TruncatedToolCallingClient(),
    )
    request = AIChatRequest(
        messages=[AIMessage(role="user", content="Enregistre la valeur 3.")]
    )

    with pytest.raises(AIOrchestrationError, match="interrompu"):
        asyncio.run(service.chat_with_tools(request, registry))

    assert executions == []
    assert registry.execution_results == ()


def test_truncated_final_answer_is_rejected_by_tool_orchestrator():
    from opencoach.ai.service import AIOrchestrationError
    from opencoach.ai.tool_engine import AIToolRegistry

    class TruncatedFinalClient:
        async def chat(self, request):
            return AIChatResult(
                model="qwen2.5:3b",
                content="Analyse partielle",
                done=True,
                done_reason="length",
            )

    service = AIService(
        AISettings(enabled=True),
        client=TruncatedFinalClient(),
    )
    request = AIChatRequest(
        messages=[AIMessage(role="user", content="Fais le bilan.")]
    )

    with pytest.raises(AIOrchestrationError, match="interrompu"):
        asyncio.run(service.chat_with_tools(request, AIToolRegistry()))


class EchoArgsForTruncationTest(BaseModel):
    value: int

def test_tool_orchestration_never_executes_more_than_maximum_rounds():
    from opencoach.ai.schemas import AIToolCall
    from opencoach.ai.service import AIOrchestrationError
    from opencoach.ai.tool_engine import AITool, AIToolRegistry

    executions = []

    class RepeatingToolCallingClient:
        def __init__(self):
            self.calls = 0

        async def chat(self, request):
            self.calls += 1
            return AIChatResult(
                model="qwen2.5:3b",
                content="",
                tool_calls=[AIToolCall(name="record", arguments={"value": self.calls})],
                done=True,
            )

    class RecordArguments(BaseModel):
        value: int

    registry = AIToolRegistry()
    registry.register(AITool(
        name="record",
        description="Enregistre une valeur de test.",
        arguments_model=RecordArguments,
        handler=lambda args: executions.append(args.value) or {"saved": True},
    ))
    client = RepeatingToolCallingClient()
    service = AIService(AISettings(enabled=True), client=client)
    request = AIChatRequest(
        messages=[AIMessage(role="user", content="Lance le test.")],
    )

    with pytest.raises(AIOrchestrationError, match="nombre maximal de tours"):
        asyncio.run(service.chat_with_tools(request, registry))

    assert client.calls == service.MAX_TOOL_ROUNDS + 1
    assert len(executions) == service.MAX_TOOL_ROUNDS
