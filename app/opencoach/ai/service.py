"""Orchestration isolée du moteur IA local."""

from __future__ import annotations

import asyncio

from opencoach.ai.client import OllamaClient
from opencoach.ai.config import AISettings
from opencoach.ai.schemas import AIChatRequest, AIChatResult


class AIServiceDisabledError(RuntimeError):
    """L'utilisation de l'IA est désactivée dans OpenCoach."""


class AIService:
    """Façade IA optionnelle, sans accès aux services métier."""

    def __init__(
        self,
        settings: AISettings,
        client: OllamaClient | None = None,
    ) -> None:
        self.settings = settings
        self.client = client or OllamaClient(settings)
        self._semaphore = asyncio.Semaphore(settings.max_concurrency)

    async def chat(self, request: AIChatRequest) -> AIChatResult:
        """Génère une réponse si la fonctionnalité est explicitement activée."""
        if not self.settings.enabled:
            raise AIServiceDisabledError(
                "Le moteur IA est désactivé. Activez OPENCOACH_AI_ENABLED explicitement."
            )

        async with self._semaphore:
            return await self.client.chat(request)
