"""Fallback explicite pour une séance non encore spécialisée."""

from .models import (
    GoalAnalysisPlan,
    GoalMetricDefinition,
    GoalType,
    MetricImportance,
)


def build_generic_goal_plan(
) -> GoalAnalysisPlan:
    return GoalAnalysisPlan(
        goal_type=GoalType.GENERIC,
        objective=(
            "Comparer les principaux éléments mesurables "
            "de la séance à la prescription disponible."
        ),
        metrics=(
            GoalMetricDefinition(
                key="duration",
                label="Durée",
                importance=MetricImportance.SECONDARY,
                reason="Volume temporel prescrit.",
            ),
            GoalMetricDefinition(
                key="distance",
                label="Distance",
                importance=MetricImportance.INFORMATIONAL,
                reason="Volume kilométrique réalisé.",
            ),
        ),
    )
