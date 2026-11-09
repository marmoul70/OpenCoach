#!/usr/bin/env python3
"""Benchmark reproductible de sélection d'outils Ollama pour OpenCoach.

Ce runner n'exécute aucun outil métier et ne lit aucune donnée personnelle.
Il mesure uniquement le premier tour de décision du modèle sur un corpus fixe.
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import ipaddress
import json
import os
import sys
import time
from urllib.parse import urlsplit
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "app"))

from opencoach.ai.client import AIProviderError, OllamaClient
from opencoach.ai.config import AISettings
from opencoach.ai.schemas import AIChatRequest, AIMessage, AIToolDefinition
from opencoach.ai.activity_tools import ActivityDetailArguments
from opencoach.ai.constraints_tools import ActiveConstraintsArguments
from opencoach.ai.coaching_tools import (
    EmptyArguments,
    PlannedSessionsArguments,
    RaceCalendarArguments,
    WeeklyPlanContextArguments,
)
from opencoach.ai.load_tools import TrainingLoadArguments
from opencoach.ai.race_tools import RacePreparationArguments
from opencoach.ai.recovery_tools import (
    RecoveryAnalysisArguments,
    RecoveryStatusArguments,
)
from opencoach.ai.trend_tools import TrainingTrendsArguments
from opencoach.ai.training_tools import TrainingHistoryArguments
from opencoach.api.ai import _COACH_SYSTEM_PROMPT


ARGUMENT_MODELS = {
    "training_history": TrainingHistoryArguments,
    "training_load": TrainingLoadArguments,
    "training_trends": TrainingTrendsArguments,
    "recovery_analysis": RecoveryAnalysisArguments,
    "recovery_status": RecoveryStatusArguments,
    "active_constraints": ActiveConstraintsArguments,
    "athlete_training_profile": EmptyArguments,
    "race_calendar": RaceCalendarArguments,
    "race_preparation_analysis": RacePreparationArguments,
    "activity_detail": ActivityDetailArguments,
    "planned_sessions": PlannedSessionsArguments,
    "weekly_plan_context": WeeklyPlanContextArguments,
}

TOOL_DESCRIPTIONS = {
    "training_history": "Bilan réel de l'historique sur nb_days jours. nb_days est obligatoire.",
    "training_load": "Charge d'entraînement OpenCoach sur nb_days jours. nb_days est obligatoire.",
    "training_trends": "Compare deux périodes. nb_days et comparison_days sont obligatoires.",
    "recovery_analysis": "Analyse descriptive OpenCoach de la récupération sur 7, 14 et 30 jours.",
    "recovery_status": "Évaluation Readiness OpenCoach pour aujourd'hui ou une date donnée.",
    "active_constraints": "Consulte les contraintes actives avant tout conseil lié à une douleur ou limitation.",
    "athlete_training_profile": "Consulte le profil sportif et les paramètres physiologiques OpenCoach.",
    "race_calendar": "Consulte les courses enregistrées dans OpenCoach.",
    "race_preparation_analysis": "Analyse la préparation d'une course ; race_id et history_days sont obligatoires.",
    "activity_detail": "Détaille une activité OpenCoach identifiée par date ou identifiant.",
    "planned_sessions": "Liste les séances planifiées sur une période explicite.",
    "weekly_plan_context": "Consulte le contexte de planification d'une semaine.",
}


def validate_local_base_url(value: str) -> str:
    """Refuse tout endpoint distant : le benchmark doit rester local."""
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("--base-url doit être une URL HTTP(S) locale valide.")
    try:
        loopback = ipaddress.ip_address(parsed.hostname).is_loopback
    except ValueError:
        loopback = parsed.hostname.lower() == "localhost"
    if not loopback or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("--base-url doit pointer vers localhost ou une adresse loopback, sans identifiants.")
    return value.rstrip("/")


def build_tool_definitions() -> list[AIToolDefinition]:
    """Construit les schémas directement depuis les modèles Pydantic métier."""
    return [
        AIToolDefinition(
            name=name,
            description=TOOL_DESCRIPTIONS[name],
            parameters=model.model_json_schema(),
        )
        for name, model in ARGUMENT_MODELS.items()
    ]


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def percentile(values: list[float], percent: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = round((len(ordered) - 1) * percent)
    return round(ordered[index], 2)


def score_response(case: dict[str, Any], tool_calls: list[dict[str, Any]], content: str) -> dict[str, Any]:
    expected = case["expected_tool_calls"]
    actual = [
        {"tool": call["name"], "arguments": call.get("arguments") or {}}
        for call in tool_calls
    ]
    exact_calls = canonical(expected) == canonical(actual)
    clarification_stage = case.get("clarification_stage", "first_turn")
    clarification_expected = case.get("expected_clarification") is not None
    clarification_observable = clarification_expected and clarification_stage == "first_turn"
    clarification_detected = (
        ("?" in content or "sur combien" in content.lower() or "quelle durée" in content.lower())
        if clarification_observable and not expected
        else (not clarification_observable or not clarification_expected)
    )
    return {
        "tool_selection_pass": exact_calls,
        "clarification_checkable": clarification_observable,
        "clarification_pass": clarification_detected if clarification_observable else None,
        "expected_tool_calls": expected,
        "actual_tool_calls": actual,
        "response_excerpt": content[:1200],
    }


async def run_case(
    *,
    client: OllamaClient,
    model: str,
    case: dict[str, Any],
    definitions: list[AIToolDefinition],
    temperature: float,
    num_predict: int,
) -> dict[str, Any]:
    request = AIChatRequest(
        messages=[
            AIMessage(role="system", content=_COACH_SYSTEM_PROMPT),
            AIMessage(role="user", content=case["prompt"]),
        ],
        tools=definitions,
        temperature=temperature,
        num_predict=num_predict,
    )
    started = time.perf_counter()
    try:
        response = await client.chat(request)
        elapsed_ms = (time.perf_counter() - started) * 1000
        calls = [
            {"name": call.name, "arguments": call.arguments}
            for call in response.tool_calls
        ]
        score = score_response(case, calls, response.content)
        return {
            "model": model,
            "case_id": case["id"],
            "category": case["category"],
            "status": "ok",
            "latency_ms": round(elapsed_ms, 2),
            **score,
        }
    except AIProviderError as exc:
        return {
            "model": model,
            "case_id": case["id"],
            "category": case["category"],
            "status": "provider_error",
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            "error": str(exc),
            "tool_selection_pass": False,
            "clarification_checkable": False,
            "clarification_pass": None,
            "expected_tool_calls": case["expected_tool_calls"],
            "actual_tool_calls": [],
            "response_excerpt": "",
        }


def summarize(rows: list[dict[str, Any]], model: str) -> dict[str, Any]:
    selected = [row for row in rows if row["model"] == model]
    valid = [row for row in selected if row["status"] == "ok"]
    latencies = [row["latency_ms"] for row in valid]
    clarification_rows = [
        row for row in valid if row["clarification_checkable"]
    ]
    return {
        "model": model,
        "runs": len(selected),
        "provider_errors": sum(row["status"] != "ok" for row in selected),
        "tool_selection_accuracy": round(
            sum(row["tool_selection_pass"] for row in valid) / len(valid), 4
        ) if valid else 0.0,
        "clarification_accuracy": round(
            sum(bool(row["clarification_pass"]) for row in clarification_rows)
            / len(clarification_rows), 4
        ) if clarification_rows else None,
        "latency_ms_p50": percentile(latencies, 0.50),
        "latency_ms_p95": percentile(latencies, 0.95),
    }


async def main_async(args: argparse.Namespace) -> int:
    args.base_url = validate_local_base_url(args.base_url)
    fixture_path = ROOT / "tests/fixtures/ai_model_evaluation_cases.json"
    cases = json.loads(fixture_path.read_text(encoding="utf-8"))
    if args.limit:
        cases = cases[:args.limit]
    definitions = build_tool_definitions()
    all_rows: list[dict[str, Any]] = []

    for model in args.models:
        settings = AISettings(
            enabled=True,
            base_url=args.base_url.rstrip("/"),
            model=model,
            connect_timeout_seconds=args.connect_timeout,
            read_timeout_seconds=args.read_timeout,
            max_concurrency=1,
        )
        client = OllamaClient(settings)
        print(f"\n=== Modèle {model} : {len(cases)} scénarios × {args.repetitions} répétitions ===")
        for repetition in range(1, args.repetitions + 1):
            for case in cases:
                row = await run_case(
                    client=client,
                    model=model,
                    case=case,
                    definitions=definitions,
                    temperature=args.temperature,
                    num_predict=args.num_predict,
                )
                row["repetition"] = repetition
                all_rows.append(row)
                marker = "OK" if row["tool_selection_pass"] else "ECHEC"
                print(
                    f"[{marker}] {model} / {case['id']} "
                    f"({row['latency_ms']} ms)"
                )
                if row["status"] == "provider_error":
                    print(f"  {row.get('error', 'Erreur fournisseur')}")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = ROOT / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"ai-benchmark-{timestamp}.json"
    csv_path = output_dir / f"ai-benchmark-{timestamp}.csv"

    summaries = [summarize(all_rows, model) for model in args.models]
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "base_url": args.base_url,
        "models": args.models,
        "repetitions": args.repetitions,
        "temperature": args.temperature,
        "num_predict": args.num_predict,
        "case_count": len(cases),
        "scope": "tool_selection_only_no_business_tool_execution",
        "summaries": summaries,
        "results": all_rows,
    }
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        fields = [
            "model", "repetition", "case_id", "category", "status",
            "latency_ms", "tool_selection_pass", "clarification_checkable",
            "clarification_pass", "expected_tool_calls", "actual_tool_calls",
            "response_excerpt", "error",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in all_rows:
            serialized = dict(row)
            for key in ("expected_tool_calls", "actual_tool_calls"):
                serialized[key] = canonical(serialized.get(key, []))
            writer.writerow(serialized)

    print("\n=== Synthèse ===")
    print(json.dumps(summaries, ensure_ascii=False, indent=2))
    print(f"\nRapport JSON : {json_path}")
    print(f"Rapport CSV  : {csv_path}")
    return 0 if all(summary["provider_errors"] == 0 for summary in summaries) else 2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--models",
        nargs="+",
        default=[os.getenv("OPENCOACH_AI_MODEL", "qwen3:8b")],
        help="Noms exacts des modèles déjà installés dans Ollama.",
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:11434")
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--limit", type=int, default=0, help="Limite de scénarios pour un essai rapide.")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--num-predict", type=int, default=512)
    parser.add_argument("--connect-timeout", type=float, default=3.0)
    parser.add_argument("--read-timeout", type=float, default=240.0)
    parser.add_argument("--output-dir", default="data/ai-benchmarks")
    args = parser.parse_args()
    try:\n        args.base_url = validate_local_base_url(args.base_url)\n    except ValueError as exc:\n        parser.error(str(exc))\n    if args.repetitions < 1 or args.limit < 0:
        parser.error("--repetitions doit être >= 1 et --limit doit être >= 0.")
    return args


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main_async(parse_args())))
