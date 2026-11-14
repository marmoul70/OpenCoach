"""Client asynchrone minimal pour l'API Ollama."""

from __future__ import annotations

from time import perf_counter

import httpx

from opencoach.ai.config import AISettings
from opencoach.ai.observability import log_ai_event, ollama_metrics
from opencoach.ai.schemas import AIChatRequest, AIChatResult, AIToolCall


def _log_generation(
    request: AIChatRequest,
    started_at: float,
    *,
    status: str,
    model: str,
    error_type: str | None = None,
    result: AIChatResult | None = None,
) -> None:
    fields = {
        "status": status,
        "provider": "ollama",
        "model": model,
        "duration_ms": round((perf_counter() - started_at) * 1000, 3),
        "error_type": error_type,
    }
    if result is not None:
        fields.update(ollama_metrics(result))
    log_ai_event("ollama_generation", trace_id=request.trace_id, **fields)


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
        started_at = perf_counter()
        timeout = httpx.Timeout(
            self.settings.read_timeout_seconds,
            connect=self.settings.connect_timeout_seconds,
        )
        payload = {
            "model": self.settings.model,
            "messages": [
                {
                    **{"role": message.role, "content": message.content},
                    **({"tool_name": message.tool_name} if message.tool_name else {}),
                    **(
                        {"tool_calls": [
                            {"function": {"name": call.name, "arguments": call.arguments}}
                            for call in message.tool_calls
                        ]}
                        if message.tool_calls else {}
                    ),
                }
                for message in request.messages
            ],
            "stream": False,
            **({"think": False} if self.settings.model.lower().startswith("qwen3") else {}),
            "options": {
                "temperature": request.temperature,
                "num_predict": request.num_predict,
            },
        }
        if request.tools:
            payload["tools"] = [
                {
                    "type": "function",
                    "function": tool.model_dump(),
                }
                for tool in request.tools
            ]

        try:
            async with httpx.AsyncClient(
                base_url=self.settings.base_url,
                timeout=timeout,
                transport=self.transport,
                trust_env=False,
            ) as client:
                response = await client.post("/api/chat", json=payload)
                response.raise_for_status()
                data = response.json()
        except httpx.TimeoutException as exc:
            _log_generation(request, started_at, status="error", model=self.settings.model, error_type=type(exc).__name__)
            raise AIProviderError(
                "Le moteur IA local n'a pas répondu dans le délai imparti."
            ) from exc
        except httpx.HTTPStatusError as exc:
            _log_generation(request, started_at, status="error", model=self.settings.model, error_type=type(exc).__name__)
            raise AIProviderError(
                f"Le moteur IA local a retourné HTTP {exc.response.status_code}."
            ) from exc
        except (httpx.HTTPError, ValueError) as exc:
            _log_generation(request, started_at, status="error", model=self.settings.model, error_type=type(exc).__name__)
            raise AIProviderError(
                "Impossible de communiquer avec le moteur IA local."
            ) from exc

        try:
            message = data["message"]
            tool_calls = [
                AIToolCall(
                    name=item["function"]["name"],
                    arguments=item["function"].get("arguments") or {},
                )
                for item in message.get("tool_calls", [])
            ]
            result = AIChatResult(
                model=data["model"],
                content=message.get("content", ""),
                tool_calls=tool_calls,
                done=data["done"],
                done_reason=data.get("done_reason"),
                total_duration=data.get("total_duration"),
                load_duration=data.get("load_duration"),
                prompt_eval_count=data.get("prompt_eval_count"),
                prompt_eval_duration=data.get("prompt_eval_duration"),
                eval_count=data.get("eval_count"),
                eval_duration=data.get("eval_duration"),
            )
            _log_generation(request, started_at, status="ok", model=result.model, result=result)
            return result
        except (KeyError, TypeError, ValueError) as exc:
            _log_generation(request, started_at, status="error", model=self.settings.model, error_type=type(exc).__name__)
            raise AIProviderError(
                "La réponse du moteur IA local ne respecte pas le contrat attendu."
            ) from exc
