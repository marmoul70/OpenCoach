"""Émission de traces IA structurées et expurgées de données métier."""

from __future__ import annotations

import json
import logging
import math
from collections import deque
from threading import Lock
from time import time
from typing import Any
from uuid import uuid4

logger = logging.getLogger("opencoach.ai.observability")

_METRIC_CAPACITY = 5_000
_metric_lock = Lock()
_metric_events: deque[dict[str, Any]] = deque(maxlen=_METRIC_CAPACITY)


def _record_metric(record: dict[str, Any]) -> None:
    duration = record.get("duration_ms")
    if not isinstance(duration, (int, float)) or not math.isfinite(duration) or duration < 0:
        return
    event = {
        "timestamp": time(),
        "event": record["event"],
        "status": record.get("status", "unknown"),
        "duration_ms": float(duration),
        "model": record.get("model"),
        "tool": record.get("tool"),
        "operation": record.get("operation"),
    }
    with _metric_lock:
        _metric_events.append(event)


def _percentile(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, math.ceil(percentile * len(ordered)) - 1)
    return round(ordered[index], 3)


def get_ai_metrics_snapshot(window_hours: int = 24) -> dict[str, Any]:
    """Retourne des agrégats bornés en mémoire, sans données utilisateur."""
    if not 1 <= window_hours <= 168:
        raise ValueError("window_hours doit être compris entre 1 et 168.")
    now = time()
    cutoff = now - window_hours * 3600
    with _metric_lock:
        events = [item.copy() for item in _metric_events if item["timestamp"] >= cutoff]

    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for item in events:
        dimension = item.get("model") or item.get("tool") or item.get("operation") or "global"
        groups.setdefault((item["event"], str(dimension)), []).append(item)

    def summarize(items: list[dict[str, Any]]) -> dict[str, Any]:
        durations = [item["duration_ms"] for item in items]
        errors = sum(item["status"] == "error" or item["status"] == "failed" for item in items)
        return {
            "count": len(items),
            "errors": errors,
            "error_rate_percent": round(errors / len(items) * 100, 2) if items else 0.0,
            "latency_ms": {
                "p50": _percentile(durations, 0.50),
                "p95": _percentile(durations, 0.95),
                "min": round(min(durations), 3) if durations else None,
                "max": round(max(durations), 3) if durations else None,
            },
        }

    breakdown = [
        {"event": event, "dimension": dimension, **summarize(items)}
        for (event, dimension), items in sorted(groups.items())
    ]
    return {
        "window_hours": window_hours,
        "retention": "process_memory",
        "capacity": _METRIC_CAPACITY,
        "sample_count": len(events),
        "total_count": len(_metric_events),
        "truncated": len(_metric_events) == _METRIC_CAPACITY,
        "summary": summarize(events),
        "breakdown": breakdown,
    }


def _clear_ai_metrics_for_tests() -> None:
    with _metric_lock:
        _metric_events.clear()

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
    _record_metric(record)
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
