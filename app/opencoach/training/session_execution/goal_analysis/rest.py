"""Objectif d'une journée ou séance de repos."""

from .models import (
    GoalAnalysisPlan,
    GoalType,
)


def build_rest_goal_plan(
) -> GoalAnalysisPlan:
    return GoalAnalysisPlan(
        goal_type=GoalType.REST,
        objective=(
            "Respecter la récupération prescrite sans "
            "ajouter de charge d'entraînement."
        ),
        metrics=(),
    )
