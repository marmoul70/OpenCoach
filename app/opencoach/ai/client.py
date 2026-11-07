"""Client asynchrone minimal pour l'API Ollama."""

from __future__ import annotations

import httpx

from opencoach.ai.config import AISettings
from opencoach.ai.schemas import AIChatRequest, AIChatResult


class AIProviderError(RuntimeError):
    """Erreur contrôlée de communication avec le fournisseur IA."""


class OllamaClient:
    """Client HTTP Ollama ; aucune dépendance au processus Ollama."""

    def __init__(
        self,
        settings: AISettings,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.settings = settings
        self.transport = transport

    async def chat(self, request: AIChatRequest) -> AIChatResult:
        """Exécute une génération non-streaming via /api/chat."""
        timeout = httpx.Timeout(
            self.settings.read_timeout_seconds,
            connect=self.settings.connect_timeout_seconds,
        )
        payload = {
            "model": self.settings.model,
            "messages": [
                message.model_dump()
                for message in request.messages
            ],
            "stream": False,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.num_predict,
            },
        }

        try:
            async with httpx.AsyncClient(
                base_url=self.settings.base_url,
                timeout=timeout,
                transport=self.transport,
                # Ignore HTTP_PROXY/HTTPS_PROXY : le moteur doit rester local.
                trust_env=False,
            ) as client:
                response = await client.post(
                    "/api/chat",
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
        except httpx.TimeoutException as exc:
            raise AIProviderError(
                "Le moteur IA local n'a pas répondu dans le délai imparti."
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise AIProviderError(
                f"Le moteur IA local a retourné HTTP {exc.response.status_code}."
            ) from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise AIProviderError(
                "Impossible de communiquer avec le moteur IA local."
            ) from exc

        try:
            message = data["message"]
            return AIChatResult(
                model=data["model"],
                content=message["content"],
                done=data["done"],
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise AIProviderError(
                "La réponse du moteur IA local ne respecte pas le contrat attendu."
            ) from exc
