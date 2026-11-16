"""Validation des affirmations sportives et de sécurité du Coach."""

from __future__ import annotations

import re


def coach_response_has_ungrounded_risk_claims(answer: str, tool_results) -> bool:
    """Rejects risky health/load claims that lack explicit structured evidence."""
    content = answer.casefold()
    results = {
        item.tool: item.data
        for item in tool_results
        if item.status == "ok" and isinstance(item.data, dict)
    }

    # A single 7-day window is not a trend. Current-vs-average is not a
    # comparable before/after measurement, so directional fatigue claims fail.
    if re.search(
        r"\bfatigue\b.{0,70}\b(?:en baisse|en hausse|diminue|augmente|"
        r"s'aggrave|s'améliore|a diminué|a augmenté)\b",
        content,
    ):
        recovery = results.get("recovery_analysis") or {}
        if not isinstance(recovery.get("trend"), dict):
            return True

    # A stress alert must be an explicit Readiness signal, not a model's
    # interpretation of a raw stress score.
    if re.search(
        r"\bstress\b.{0,70}\b(?:en alerte|alerte|inqui[eé]tant|critique|alarmant)\b",
        content,
    ):
        recovery_status = results.get("recovery_status") or {}
        signals = recovery_status.get("signals", [])
        supported = any(
            isinstance(signal, dict)
            and "stress" in str(signal.get("metric", "")).casefold()
            and str(signal.get("level", "")).casefold()
                in {"warning", "critical", "alert", "high"}
            for signal in signals
        )
        if not supported:
            return True

    # The load service deliberately exposes no low/high classification or
    # individual threshold. The model must not invent one.
    if re.search(
        r"\b(?:charge|charge de travail|charge d'entraînement)\b"
        r".{0,45}\b(?:basse|faible|élevée|haute|excessive|maîtrisée)\b",
        content,
    ):
        load = results.get("training_load") or {}
        if not load.get("classification"):
            return True

    # Do not cancel a planned session unless a dated OpenCoach constraint
    # explicitly prohibits it. Generic stress/fatigue wording is insufficient.
    if re.search(
        r"\b(?:ne pas|pas)\s+(?:faire|prendre|effectuer|maintenir)\s+"
        r"(?:cette\s+|la\s+)?(?:prochaine\s+)?s[eé]ance\b|"
        r"\bannul(?:er|e)\s+(?:cette\s+|la\s+)?s[eé]ance\b|"
        r"\bne pas reprendre\b",
        content,
    ):
        constraints_data = results.get("active_constraints") or {}
        restriction = constraints_data.get("running_restriction")
        explicitly_blocked = (
            isinstance(restriction, dict)
            and restriction.get("blocked") is True
        )
        if not explicitly_blocked:
            return True

    # A profile is complete only when the tool reports status=ok and no missing fields.
    if re.search(
        r"\bprofil\b.{0,55}\b(?:correctement|compl[eè]tement|parfaitement)\s+"
        r"(?:d[eé]fini|renseign[eé]|configur[eé])\b",
        content,
    ):
        profile = results.get("athlete_training_profile") or {}
        if profile.get("status") != "ok" or profile.get("missing_profile_fields"):
            return True

    return False

