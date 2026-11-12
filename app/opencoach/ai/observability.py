"""Émission de traces IA structurées et expurgées de données métier."""

from __future__ import annotations

import json
import logging
from typing import Any
from uuid import uuid4

logger = logging.getLogger("opencoach.ai.observability")

# Liste blanche stricte : aucun prompt, argument, résultat métier, identifiant
# d'athlète, URL fournisseur ou secret ne peut entrer dans une trace.
_ALLOWED_FIELDS = {
    "status", "operation", "provider", "model", "duration_ms",
    "ollama_total_duration_ms", "ollama_load_duration_ms",
    "prompt_eval_count", "prompt_eval_duration_ms", "eval_count",
    "eval_duration_ms", "tool", "business_tool_executed", "error_type",
}


def new_ai_trace_id() -> str:
    """Crée un identifiant aléatoire non dérivé d'une donnée utilisateur."""
    return uuid4().hex


def _duration_ms(value: int | None) -> float | None:
    """Convertit les durées natives Ollama (nanosecondes) en millisecondes."""
    if value is None:
        return None
    return round(value / 1_000_000, 3)


def log_ai_event(
    event: str,
    *,
    trace_id: str | None = None,
    **fields: Any,
) -> None:
    """Écrit une ligne JSON limitée à une liste blanche de métadonnées."""
    record: dict[str, Any] = {
        "event": event,
        "trace_id": trace_id or new_ai_trace_id(),
    }
    for key in _ALLOWED_FIELDS:
        value = fields.get(key)
        if value is not None:
            record[key] = value
    logger.info("opencoach_ai_observability %s", json.dumps(
        record, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ))


def ollama_metrics(result: Any) -> dict[str, Any]:
    """Retourne les métriques techniques Ollama sans contenu de génération."""
    return {
        "ollama_total_duration_ms": _duration_ms(result.total_duration),
        "ollama_load_duration_ms": _duration_ms(result.load_duration),
        "prompt_eval_count": result.prompt_eval_count,
        "prompt_eval_duration_ms": _duration_ms(result.prompt_eval_duration),
        "eval_count": result.eval_count,
        "eval_duration_ms": _duration_ms(result.eval_duration),
    }
