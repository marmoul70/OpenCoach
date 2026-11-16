"""Contrôle Coach des prérequis à une recommandation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from opencoach.coaching.recommendation_safety import (
    blocked_running_recommendation_message,
)


def recommendation_execution_block_message(
    recommendation_requested: bool,
    tool_results: Sequence[Any],
) -> str | None:
    """Empêche une recommandation si les prérequis de sécurité sont absents.

    Les résultats sont des enveloppes d'exécution fournies par les adaptateurs.
    Cette fonction ne calcule aucune donnée sportive : elle vérifie que les
    capacités Coach nécessaires ont répondu et applique leur restriction.
    """
    if not recommendation_requested:
        return None

    results = {
        item.tool: item
        for item in tool_results
    }

    required = ("active_constraints", "recovery_status")
    for tool_name in required:
        result = results.get(tool_name)
        if result is None or result.status != "ok" or not isinstance(result.data, Mapping):
            return (
                "Je n'ai pas pu consulter les contraintes ou la récupération dans "
                "OpenCoach. Je ne peux donc pas te recommander de séance sur cette "
                "base. Réessaie après vérification de la disponibilité du service."
            )

    constraints = results["active_constraints"].data
    restriction = constraints.get("running_restriction")
    return blocked_running_recommendation_message(
        restriction if isinstance(restriction, Mapping) else None
    )
