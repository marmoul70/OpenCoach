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
    "next_planned_session",
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
    evidence_history: list[str] | None = None,
) -> frozenset[str]:
    # L'historique de routage peut être réduit à l'intention initiale ;
    # les preuves temporelles doivent néanmoins conserver tous les tours utilisateur.
    period_messages = [*(evidence_history if evidence_history is not None else (history or [])), question]
    periods = extract_explicit_periods(
        period_messages,
        assistant_history,
    )
    filtered = set(names)
    if len(periods) < 1:
        filtered.difference_update(PERIOD_REQUIRED_TOOLS - {"training_trends"})
    else:
        period_limits = {
            "training_history": (1, 365),
            "training_load": (1, 90),
            "race_preparation_analysis": (7, 180),
        }
        for tool_name, (minimum, maximum) in period_limits.items():
            if tool_name in filtered and not minimum <= periods[-1] <= maximum:
                filtered.discard(tool_name)
    if len(periods) < 2 or any(
        not 1 <= period <= 180 for period in periods[-2:]
    ):
        filtered.discard("training_trends")
    date_range = extract_explicit_date_range(
        period_messages,
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
    evidence_history: list[str] | None = None,
) -> frozenset[str]:
    """Sélectionne les outils utiles et masque les outils temporels incomplets."""
    current = _normalize(question.strip())
    if not current:
        return _filter_period_tools(
            FALLBACK_SAFE_TOOLS, question, history, assistant_history, evidence_history
        )

    # Questions générales et demandes d'écriture interdites : aucun outil métier.
    no_tool_patterns = (
        "explique-moi la difference", "explique moi la difference",
        "quelle est la difference", "qu'est-ce que", "quest-ce que",
        "explique-moi ce qu'est", "explique moi ce qu est",
        "c'est quoi un", "c est quoi un", "c'est quoi une", "c est quoi une",
        "c'est quoi le trail", "que signifie",
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
        (("historique", "seances realisees", "entrainements realises", "mes entrainements", "mes activites", "bilan de mes sorties", "mes sorties", "bilan de ma semaine", "bilan de la semaine", "bilan hebdomadaire"), ("training_history",)),
        (("charge", "mon atl", "ctl", "tsb", "mon volume", "volume d entrainement"), ("training_load",)),
        (("recuperation", "recup", "sommeil", "hrv", "variabilite", "fatigue", "fatiguee", "fatigue"), ("recovery_analysis", "recovery_status")),
        (("comment je vais", "comment vais-je", "comment est ma forme", "comment va ma forme", "ou j en suis", "bilan de forme", "suis-je en forme"), ("recovery_analysis", "recovery_status", "weekly_plan_context")),
        (("tendance", "evolution", "progression", "compare", "comparaison", "progres"), ("training_trends",)),
        (("activite du", "activite", "detail de", "detaille ma seance", "ma seance du", "seance du", "derniere activite", "activite la plus recente", "derniere sortie", "ma sortie du", "intervalles", "fractionne realise"), ("activity_detail",)),
        (("course", "ultra", "trail", "dossard", "competition", "calendrier des courses", "objectif de course"), ("race_calendar",)),
        (("preparation", "preparer", "prepare", "objectif chrono", "temps cible"), ("race_calendar", "race_preparation_analysis")),
        (("prochaine seance", "prochain entrainement", "quelle seance ensuite", "seance suivante"), ("next_planned_session",)),
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

    # Une analyse de charge utile au coaching doit disposer du cadre
    # hebdomadaire et des signaux de récupération. Ces outils n'ont pas de
    # période obligatoire ; ils ne sont ajoutés que si training_load est
    # effectivement autorisé par une durée explicitement fournie.
    filtered = _filter_period_tools(
        selected, question, history, assistant_history, evidence_history
    )
    if "training_load" in filtered:
        filtered = frozenset({
            *filtered,
            "weekly_plan_context",
            "recovery_analysis",
            "recovery_status",
        })
    return filtered

