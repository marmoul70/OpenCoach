"""Routage déterministe et conservateur des outils du coach.

Le routeur ne lit aucune donnée athlète et n'exécute aucun outil. Il réduit
uniquement le catalogue présenté au modèle à partir de l'intention explicite.
En cas d'incertitude, il conserve le catalogue général, mais masque les outils dont les paramètres temporels obligatoires ne sont pas étayés.
"""
from __future__ import annotations

import unicodedata

from opencoach.ai.argument_evidence import (
    extract_explicit_date_range,
    extract_explicit_periods,
)


ALL_COACH_TOOLS = frozenset({
    "athlete_training_profile",
    "active_constraints",
    "weekly_plan_context",
    "race_calendar",
    "race_preparation_analysis",
    "planned_sessions",
    "session_execution_review",
    "activity_detail",
    "training_history",
    "training_load",
    "recovery_status",
    "recovery_analysis",
    "training_trends",
    "propose_profile_data",
})


PERIOD_REQUIRED_TOOLS = frozenset({
    "training_history",
    "training_load",
    "training_trends",
    "race_preparation_analysis",
})
FALLBACK_SAFE_TOOLS = ALL_COACH_TOOLS - {"propose_profile_data"}


def _normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value.lower())
    return "".join(char for char in value if not unicodedata.combining(char))


def _filter_period_tools(
    names: set[str] | frozenset[str],
    question: str,
    history: list[str] | None,
    assistant_history: list[str] | None,
) -> frozenset[str]:
    periods = extract_explicit_periods(
        [*(history or []), question],
        assistant_history,
    )
    filtered = set(names)
    if len(periods) < 1:
        filtered.difference_update(PERIOD_REQUIRED_TOOLS - {"training_trends"})
    if len(periods) < 2:
        filtered.discard("training_trends")
    date_range = extract_explicit_date_range(
        [*(history or []), question],
        assistant_history,
    )
    if date_range is None:
        filtered.discard("planned_sessions")
    return frozenset(filtered)


def select_coach_tools(
    question: str,
    *,
    history: list[str] | None = None,
    assistant_history: list[str] | None = None,
) -> frozenset[str]:
    """Sélectionne les outils utiles et masque les outils temporels incomplets."""
    current = _normalize(question.strip())
    if not current:
        return _filter_period_tools(
            FALLBACK_SAFE_TOOLS, question, history, assistant_history
        )

    # Questions générales et demandes d'écriture interdites : aucun outil métier.
    no_tool_patterns = (
        "explique-moi la difference", "explique moi la difference",
        "quelle est la difference", "qu'est-ce que", "quest-ce que",
        "definition de", "explique le principe",
    )
    if any(pattern in current for pattern in no_tool_patterns):
        return frozenset()
    if any(term in current for term in (
        "decale automatiquement", "modifie automatiquement",
        "supprime automatiquement", "ecris directement dans coros",
        "modifie mon planning", "change mon planning automatiquement",
    )):
        return frozenset()
    if "directement mes donnees coros" in current or "directement coros" in current:
        return frozenset()

    # Les messages antérieurs ne servent qu'à résoudre un suivi très court.
    context = current
    if len(current.split()) <= 5 and history:
        context = _normalize(" ".join([*history[-2:], question]))

    selected: set[str] = set()
    groups: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...] = (
        (("historique", "seances realisees", "entrainements realises", "bilan de mes sorties", "mes sorties"), ("training_history",)),
        (("charge", "mon atl", "ctl", "tsb", "mon volume", "volume d entrainement"), ("training_load",)),
        (("recuperation", "recup", "sommeil", "hrv", "variabilite", "fatigue", "fatiguee", "fatigue"), ("recovery_analysis", "recovery_status")),
        (("tendance", "evolution", "progression", "compare", "comparaison", "progres"), ("training_trends",)),
        (("activite du", "activite", "detail de", "detaille ma seance", "ma seance du", "seance du", "derniere sortie", "ma sortie du", "intervalles", "fractionne realise"), ("activity_detail",)),
        (("course", "ultra", "trail", "dossard", "competition", "calendrier des courses", "objectif de course"), ("race_calendar",)),
        (("preparation", "preparer", "prepare", "objectif chrono", "temps cible"), ("race_calendar", "race_preparation_analysis")),
        (("planning", "planifie", "programme", "semaine", "seances prevues", "prochaines seances"), ("weekly_plan_context", "planned_sessions")),
        (("seance prevue", "seance realisee", "execution", "respecte mon plan", "ecart au plan"), ("planned_sessions", "session_execution_review")),
        (("blessure", "douleur", "mal au", "tendon", "je suis malade", "maladie", "indisponible", "contrainte", "genant"), ("active_constraints",)),
        (("zone cardiaque", "zones cardiaques", "vma", "fc max", "frequence cardiaque", "seuil"), ("athlete_training_profile",)),
        (("profil", "mes informations", "mes caracteristiques", "equipement", "chaussures"), ("athlete_training_profile",)),
    )
    for keywords, tools in groups:
        if any(keyword in context for keyword in keywords):
            selected.update(tools)

    # La proposition de modification du profil n'est exposée que si l'utilisateur
    # communique explicitement une nouvelle donnée durable.
    profile_update_terms = (
        "mon poids est", "je pese", "ma vma est", "ma fc max est",
        "je change de chaussures", "mon objectif est",
        "je suis disponible", "je ne suis plus disponible",
    )
    if any(term in context for term in profile_update_terms):
        selected.add("propose_profile_data")

    if not selected:
        return _filter_period_tools(
            FALLBACK_SAFE_TOOLS, question, history, assistant_history
        )

    # Les contraintes sont toujours ajoutées dès qu'une recommandation ou une
    # décision d'entraînement est demandée, même si la douleur est implicite.
    recommendation_terms = ("que faire", "quelle seance", "quel entrainement", "conseille", "recommande", "ajuste", "adapter")
    if any(term in context for term in recommendation_terms):
        selected.add("active_constraints")
        selected.update(("recovery_analysis", "recovery_status"))

    # Même en cas d'intention reconnue, seuls les outils dont les
    # paramètres temporels sont étayés restent disponibles.
    return _filter_period_tools(
        selected, question, history, assistant_history
    )

