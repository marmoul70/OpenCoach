"""Orchestration isolée du moteur IA local."""

from __future__ import annotations

import asyncio
import json

from opencoach.ai.client import OllamaClient
from opencoach.ai.config import AISettings
from opencoach.ai.schemas import AIChatRequest, AIChatResult, AIMessage, AIToolDefinition
from opencoach.ai.tool_engine import AIToolRegistry


class AIServiceDisabledError(RuntimeError):
    """L'utilisation de l'IA est désactivée dans OpenCoach."""


class AIService:
    """Façade IA optionnelle, sans accès direct aux services métier."""

    MAX_TOOL_ROUNDS = 3
    MAX_TOOL_CALLS_PER_ROUND = 3
    MAX_TOOL_RESULT_CHARS = 12_000

    def __init__(
        self,
        settings: AISettings,
        client: OllamaClient | None = None,
    ) -> None:
        self.settings = settings
        self.client = client or OllamaClient(settings)
        self._semaphore = asyncio.Semaphore(settings.max_concurrency)

    async def chat(self, request: AIChatRequest) -> AIChatResult:
        """Génère une réponse sans outil."""
        if not self.settings.enabled:
            raise AIServiceDisabledError(
                "Le moteur IA est désactivé. Activez OPENCOACH_AI_ENABLED explicitement."
            )
        async with self._semaphore:
            return await self.client.chat(request)

    async def chat_with_tools(
        self,
        request: AIChatRequest,
        registry: AIToolRegistry,
    ) -> AIChatResult:
        """Exécute une boucle d'outils bornée et validée côté Python."""
        if not self.settings.enabled:
            raise AIServiceDisabledError(
                "Le moteur IA est désactivé. Activez OPENCOACH_AI_ENABLED explicitement."
            )

        definitions = [
            AIToolDefinition(
                name=item["name"],
                description=item["description"],
                parameters=item["parameters"],
            )
            for item in registry.definitions()
        ]
        messages = list(request.messages)
        async with self._semaphore:
            for _ in range(self.MAX_TOOL_ROUNDS + 1):
                result = await self.client.chat(
                    request.model_copy(update={"messages": messages, "tools": definitions})
                )
                if not result.tool_calls:
                    return result
                if len(result.tool_calls) > self.MAX_TOOL_CALLS_PER_ROUND:
                    raise RuntimeError("Le modèle a dépassé le nombre d'appels d'outils autorisé.")
                messages.append(
                    AIMessage(
                        role="assistant",
                        content=result.content,
                        tool_calls=result.tool_calls,
                    )
                )
                for call in result.tool_calls:
                    tool_result = registry.execute(call.name, call.arguments)
                    serialized = json.dumps(
                        tool_result.model_dump(mode="json"),
                        ensure_ascii=False,
                    )
                    if len(serialized) > self.MAX_TOOL_RESULT_CHARS:
                        serialized = json.dumps(
                            {"tool": call.name, "status": "failed",
                             "error": "Résultat trop volumineux.", "metadata": {}},
                            ensure_ascii=False,
                        )
                    messages.append(
                        AIMessage(role="tool", tool_name=call.name, content=serialized)
                    )
            raise RuntimeError("Le nombre maximal de tours d'outils a été atteint.")
