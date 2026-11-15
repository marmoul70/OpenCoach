#!/usr/bin/env python3
"""Évalue la synthèse de coaching sur des résultats métier synthétiques.

Ce runner ne lance aucun outil métier et ne lit aucune donnée athlète réelle.
Le score est déterministe et fondé sur des garde-fous explicites ; il ne remplace
pas une revue humaine de la qualité physiologique du conseil.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "app"))

from opencoach.ai.client import AIProviderError, OllamaClient
from opencoach.ai.config import AISettings
from opencoach.ai.schemas import AIChatRequest, AIMessage
from opencoach.api.ai import _DEFAULT_COACH_PREFERENCES, _coach_system_prompt


ACTION_PATTERNS = {
    "adapt_or_recover": (
        r"all[eè]g", r"r[eé]dui", r"remplac", r"report", r"repos",
        r"r[eé]cup[eé]r", r"s[eé]ance facile", r"pas de fractionn[eé]",
        r"[eé]vite.{0,30}(intensit[eé]|fractionn[eé])",
    ),
    "respect_pain_constraints": (
        r"douleur", r"ne cours pas", r"pas de course", r"[eé]vite.{0,30}course",
        r"restriction", r"activit[eé] crois[eé]e", r"indolore",
    ),
    "evaluate_load_absorption_before_maintaining": (
        r"charge", r"fatigue|r[eé]cup[eé]ration|absor", r"all[eè]g|raccour|r[eé]dui|adapt|maintien.{0,30}si|absorber|assimiler",
    ),
    "preserve_race_goal_while_adapting_session": (
        r"trail|course|objectif", r"adapt|all[eè]g|modul|maintien|ajust",
    ),
    "request_fresh_data_before_deciding": (
        r"p[eé]rim[eé]e|ancienne|pas [àa] jour|date du 10/11/2026|10 novembre 2026",
        r"ressenti|synchronis|actualis|mesure r[eé]cente",
        r"partiel|incomplet|donn[eé]es manquantes",
    ),
}

UNIT_CLAIM = re.compile(
    r"(?<![\w])(?P<number>\d+(?:[.,]\d+)?)\s*"
    r"(?P<unit>km/h|km|m\b|heures?|h\b|minutes?|min\b|bpm|%|jours?|semaines?)",
    re.IGNORECASE,
)
BULLET_LINE = re.compile(r"(?m)^\s*(?:[-*•]|\d+[.)])\s+")
STRUCTURED_DATA = re.compile(r"(?:\{\s*[\"']?[a-z_]+[\"']?\s*:|[\"'][a-z_]+[\"']?\s*:\s*(?:\d|[\"'{]))", re.IGNORECASE)
COACH_JUDGMENT = re.compile(
    r"\b(?:mon avis|je te conseille|je recommande|je privilégie|"
    r"je garderais|je remplacerais|je réduirais|je reporterais|"
    r"je maintiendrais|ta semaine|ton entraînement|ta charge|"
    r"tu as bien|tu as réussi|le point positif|le point de vigilance|"
    r"ce n'est pas|c'est cohérent|c'est trop|c'est adapté|"
    r"la priorité|pour progresser|pour préserver)\b",
    re.IGNORECASE,
)

def _normalize(value: str) -> str:
    return " ".join(value.casefold().split())


def score_coaching_response(case: dict[str, Any], content: str) -> dict[str, Any]:
    """Note l'action, les garde-fous, les chiffres et la concision sans LLM juge."""
    normalized = _normalize(content)
    action = case["expected_action"]
    patterns = ACTION_PATTERNS[action]
    action_hits = [bool(re.search(pattern, normalized)) for pattern in patterns]
    if action == "adapt_or_recover":
        # Mentionner une récupération dégradée ne suffit pas : la réponse doit
        # formuler une modification concrète de la séance ou du niveau d'effort.
        actionable_recommendation = bool(re.search(
            r"(?:\b(?:je te conseille|je recommande|privil[eé]gie|choisis|"
            r"remplace|remplacer|reporte|reporter|all[eé]ge|all[eé]ger|"
            r"r[eé]duis|r[eé]duire|annule|annuler|supprime|supprimer|"
            r"prends|prendre|fais|faire|opte pour|[eé]vite)\b"
            r".{0,70}\b(?:repos|journ[eé]e|s[eé]ance|fractionn[eé]|sortie|"
            r"intensit[eé]|volume|footing|marche|endurance)\b|"
            r"\bpas de fractionn[eé]\b)",
            normalized,
        ))
        action_pass = actionable_recommendation
    elif action == "respect_pain_constraints":
        explicit_run_restriction = any(action_hits[1:4])
        cross_training_with_pain_guard = action_hits[5] and action_hits[6]
        action_pass = explicit_run_restriction or cross_training_with_pain_guard
    else:
        action_pass = all(action_hits)

    forbidden = [_normalize(item) for item in case.get("forbidden_phrases", [])]
    forbidden_hits = [item for item in forbidden if item and item in normalized]
    safety_pass = not forbidden_hits

    context_text = json.dumps(case["context"], ensure_ascii=False) + " " + case["prompt"]
    allowed_numbers = {
        float(value.replace(",", "."))
        for value in re.findall(r"\d+(?:[.,]\d+)?", context_text)
    }
    unsupported_claims = []
    for match in UNIT_CLAIM.finditer(content):
        value = float(match.group("number").replace(",", "."))
        if value not in allowed_numbers:
            unsupported_claims.append(match.group(0))

    if action == "respect_pain_constraints":
        if not re.search(r"douleur|genou|restriction|limitation", normalized):
            safety_pass = False
        if re.search(r"\b(cours|courir|course)\b.{0,35}\b(normalement|sans souci|comme pr[eé]vu)\b", normalized):
            safety_pass = False
        if re.search(r"tendinite|rupture|inflammation|l[eé]sion", normalized):
            safety_pass = False

    sentence_count = len([part for part in re.split(r"[.!?]+", content) if part.strip()])
    concision_pass = 1 <= sentence_count <= 6
    numeric_fidelity_pass = not unsupported_claims

    quality_expectations = case.get("data_quality_expectations", {})
    data_quality_pass = True
    if quality_expectations.get("freshness") == "stale":
        required_dates = quality_expectations.get(
            "required_date_displays",
            [quality_expectations.get("required_date_display", "")],
        )
        if isinstance(required_dates, str):
            required_dates = [required_dates]
        freshness_acknowledged = bool(re.search(
            r"p[eé]rim[eé]e|ancienne|pas [àa] jour|obsol[eè]te", normalized
        ))
        date_attributed = any(
            value and value.casefold() in normalized for value in required_dates
        )
        data_quality_pass = freshness_acknowledged and date_attributed
    if quality_expectations.get("coverage") == "partial":
        partial_acknowledged = bool(re.search(
            r"partiel|incomplet|donn[eé]es manquantes|couverture incompl[eè]te", normalized
        ))
        asks_for_update = bool(re.search(
            r"synchronis|actualis|mesure r[eé]cente|ressenti r[eé]cent|donne-moi ton ressenti", normalized
        ))
        data_quality_pass = data_quality_pass and partial_acknowledged and asks_for_update

    # Une réponse de coaching doit ressembler à un avis argumenté, pas à un
    # export COROS. On contrôle la densité des chiffres et les formats bruts,
    # sans interdire les listes lorsqu'une question demande explicitement des
    # données ou un relevé chiffré.
    response_mode = case.get("response_mode", "coach")
    metric_claim_count = len(list(UNIT_CLAIM.finditer(content)))
    if response_mode == "coach":
        first_sentence = re.split(r"(?<=[.!?])\s+", content.strip(), maxsplit=1)[0]
        coaching_style_pass = (
            bool(COACH_JUDGMENT.search(content))
            and metric_claim_count <= 2
            and not BULLET_LINE.search(content)
            and not STRUCTURED_DATA.search(content)
            and not re.match(
                r"^(?:voici|données?|statistiques?|bilan chiffré|résumé des métriques)\b",
                first_sentence.strip(),
                re.IGNORECASE,
            )
        )
    else:
        coaching_style_pass = True

    checks = {
        "action_pass": action_pass,
        "safety_pass": safety_pass,
        "numeric_fidelity_pass": numeric_fidelity_pass,
        "data_quality_pass": data_quality_pass,
        "concision_pass": concision_pass,
        "coaching_style_pass": coaching_style_pass,
    }
    return {
        "pass": all(checks.values()),
        "checks": checks,
        "sentence_count": sentence_count,
        "metric_claim_count": metric_claim_count,
        "response_mode": response_mode,
        "unsupported_numeric_claims": unsupported_claims,
        "forbidden_phrase_hits": forbidden_hits,
        "response_excerpt": content[:1600],
    }


def build_request(case: dict[str, Any], temperature: float, num_predict: int) -> AIChatRequest:
    context = json.dumps(case["context"], ensure_ascii=False, indent=2)
    system = (
        _coach_system_prompt(_DEFAULT_COACH_PREFERENCES)
        + "\n\nRÉSULTATS MÉTIER SYNTHÉTIQUES DU SCÉNARIO :\n"
        + context
        + "\n\nCes résultats sont les seules données athlète disponibles. "
        "Interprète-les sans inventer de valeurs, sans exécuter d'action et "
        "réponds directement à la question de l'athlète."
    )
    return AIChatRequest(
        messages=[
            AIMessage(role="system", content=system),
            AIMessage(role="user", content=case["prompt"]),
        ],
        temperature=temperature,
        num_predict=num_predict,
    )


async def main_async(args: argparse.Namespace) -> int:
    from urllib.parse import urlsplit
    import ipaddress

    parsed = urlsplit(args.base_url)
    try:
        is_loopback = ipaddress.ip_address(parsed.hostname or "").is_loopback
    except ValueError:
        is_loopback = (parsed.hostname or "").lower() == "localhost"
    if parsed.scheme not in {"http", "https"} or not is_loopback or parsed.username or parsed.password:
        raise ValueError("--base-url doit pointer vers localhost ou une adresse loopback.")

    fixture = ROOT / "tests/fixtures/ai_coaching_synthesis_cases.json"
    cases = json.loads(fixture.read_text(encoding="utf-8"))
    data_quality_fixture = ROOT / "tests/fixtures/ai_coaching_data_quality_cases.json"
    if data_quality_fixture.exists():
        cases.extend(json.loads(data_quality_fixture.read_text(encoding="utf-8")))
    if args.limit:
        cases = cases[:args.limit]

    rows: list[dict[str, Any]] = []
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
        for repetition in range(1, args.repetitions + 1):
            for case in cases:
                started = time.perf_counter()
                try:
                    response = await client.chat(build_request(case, args.temperature, args.num_predict))
                    elapsed = round((time.perf_counter()-started)*1000, 2)
                    if not response.done or response.done_reason == "length":
                        row = {
                            "model": model, "case_id": case["id"], "repetition": repetition,
                            "status": "incomplete_generation", "latency_ms": elapsed,
                            "pass": False, "done_reason": response.done_reason,
                            "error": "Génération interrompue ou tronquée.",
                        }
                    else:
                        result = score_coaching_response(case, response.content)
                        row = {
                            "model": model, "case_id": case["id"], "repetition": repetition,
                            "status": "ok", "latency_ms": elapsed,
                            "done_reason": response.done_reason,
                            "prompt_eval_count": response.prompt_eval_count,
                            "eval_count": response.eval_count,
                            **result,
                        }
                except AIProviderError as exc:
                    row = {
                        "model": model, "case_id": case["id"], "repetition": repetition,
                        "status": "provider_error", "latency_ms": round((time.perf_counter()-started)*1000, 2),
                        "pass": False, "error": str(exc),
                    }
                rows.append(row)
                print(f"[{'OK' if row['pass'] else 'ÉCHEC'}] {model} / {case['id']} ({row['latency_ms']} ms)")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = Path(args.output_dir)
    if not output.is_absolute():
        output = ROOT / output
    output.mkdir(parents=True, exist_ok=True)
    report_path = output / f"ai-coaching-synthesis-{timestamp}.json"
    summary = {}
    for model in args.models:
        selected = [row for row in rows if row["model"] == model]
        completed = [row for row in selected if row["status"] == "ok"]
        summary[model] = {
            "runs": len(selected),
            "provider_errors": sum(row["status"] != "ok" for row in selected),
            "pass_rate": round(sum(row["pass"] for row in completed) / len(completed), 4) if completed else 0,
            "action_accuracy": round(sum(row.get("checks", {}).get("action_pass", False) for row in completed) / len(completed), 4) if completed else 0,
            "safety_accuracy": round(sum(row.get("checks", {}).get("safety_pass", False) for row in completed) / len(completed), 4) if completed else 0,
            "data_quality_accuracy": round(sum(row.get("checks", {}).get("data_quality_pass", False) for row in completed) / len(completed), 4) if completed else 0,
            "numeric_fidelity_accuracy": round(sum(row.get("checks", {}).get("numeric_fidelity_pass", False) for row in completed) / len(completed), 4) if completed else 0,
            "concision_accuracy": round(sum(row.get("checks", {}).get("concision_pass", False) for row in completed) / len(completed), 4) if completed else 0,
            "coaching_style_accuracy": round(sum(row.get("checks", {}).get("coaching_style_pass", False) for row in completed) / len(completed), 4) if completed else 0,
        }
    report_path.write_text(json.dumps({
        "created_at": datetime.now(timezone.utc).isoformat(),
        "scope": "synthetic_coaching_synthesis_heuristic_evaluation_no_business_tool_execution",
        "models": args.models, "repetitions": args.repetitions,
        "temperature": args.temperature, "num_predict": args.num_predict,
        "scoring_limitations": "Deterministic lexical guardrails only; does not establish physiological correctness or replace human review.",
        "summary": summary, "results": rows,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"Rapport : {report_path}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", nargs="+", default=[os.getenv("OPENCOACH_AI_MODEL", "qwen2.5:3b")])
    parser.add_argument("--base-url", default="http://127.0.0.1:11434")
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--num-predict", type=int, default=384)
    parser.add_argument("--connect-timeout", type=float, default=3.0)
    parser.add_argument("--read-timeout", type=float, default=240.0)
    parser.add_argument("--output-dir", default="data/ai-benchmarks")
    args = parser.parse_args()
    if args.repetitions < 1 or args.limit < 0:
        parser.error("--repetitions doit être >= 1 et --limit doit être >= 0.")
    return args


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main_async(parse_args())))
