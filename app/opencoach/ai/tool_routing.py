"""Routage déterministe et conservateur des outils du coach.

Le routeur ne lit aucune donnée athlète et n'exécute aucun outil. Il réduit
uniquement le catalogue présenté au modèle à partir de l'intention explicite.
En cas d'incertitude, il conserve le catalogue complet.
"""
from __future__ import annotations

import unicodedata


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


def _normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value.lower())
    return "".join(char for char in value if not unicodedata.combining(char))


def select_coach_tools(question: str, *, history: list[str] | None = None) -> frozenset[str]:
    """Sélectionne les outils utiles ; renvoie tout le catalogue si ambigu."""
    current = _normalize(question.strip())
    if not current:
        return ALL_COACH_TOOLS

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
        (("activite du", "detail de", "intervalles", "fractionne realise", "ma sortie du"), ("activity_detail",)),
        (("course", "ultra", "trail", "dossard", "competition", "calendrier des courses", "objectif de course"), ("race_calendar",)),
        (("preparation", "preparer", "prepare", "objectif chrono", "temps cible"), ("race_calendar", "race_preparation_analysis")),
        (("planning", "planifie", "programme", "semaine", "seances prevues", "prochaines seances"), ("weekly_plan_context", "planned_sessions")),
        (("seance prevue", "seance realisee", "execution", "respecte mon plan", "ecart au plan"), ("planned_sessions", "session_execution_review")),
        (("blessure", "douleur", "malade", "maladie", "indisponible", "contrainte", "genant"), ("active_constraints",)),
        (("zone cardiaque", "zones cardiaques", "vma", "fc max", "frequence cardiaque", "seuil"), ("athlete_training_profile",)),
        (("profil", "mes informations", "mes caracteristiques", "equipement", "chaussures"), ("athlete_training_profile",)),
    )
    for keywords, tools in groups:
        if any(keyword in context for keyword in keywords):
            selected.update(tools)

    # Proposition de donnée durable : seule capacité d'écriture contrôlée.
    selected.add("propose_profile_data")

    if not selected or len(selected) == 1:
        return ALL_COACH_TOOLS

    # Les contraintes sont toujours ajoutées dès qu'une recommandation ou une
    # décision d'entraînement est demandée, même si la douleur est implicite.
    recommendation_terms = ("que faire", "quelle seance", "quel entrainement", "conseille", "recommande", "ajuste", "adapter")
    if any(term in context for term in recommendation_terms):
        selected.add("active_constraints")
        selected.update(("recovery_analysis", "recovery_status"))

    return frozenset(selected)
