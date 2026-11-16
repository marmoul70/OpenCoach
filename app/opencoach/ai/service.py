"""Orchestration isolée du moteur IA local."""

from __future__ import annotations

import asyncio

from opencoach.ai.client import OllamaClient
from opencoach.ai.config import AISettings
from opencoach.ai.schemas import AIChatRequest, AIChatResult


class AIServiceDisabledError(RuntimeError):
    """L'utilisation de l'IA est désactivée dans OpenCoach."""


class AIService:
    """Façade IA optionnelle, sans accès direct aux services métier."""

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
        if request.tools:
            raise ValueError(
                "Le moteur IA ne peut pas sélectionner ni exécuter les capacités Coach. "
                "Le plan d'exécution déterministe doit fournir les résultats à synthétiser."
            )
        async with self._semaphore:
            return await self.client.chat(request)
