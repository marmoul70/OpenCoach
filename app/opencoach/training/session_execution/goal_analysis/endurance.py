"""Objectif des séances continues d'endurance."""

from __future__ import annotations

from .models import (
    GoalAnalysisPlan,
    GoalMetricDefinition,
    GoalType,
    MetricImportance,
)


def build_endurance_goal_plan(
) -> GoalAnalysisPlan:
    """Construit le plan d'analyse d'une séance d'endurance."""

    return GoalAnalysisPlan(
        goal_type=GoalType.ENDURANCE,
        objective=(
            "Accumuler le volume prescrit en maintenant "
            "l'intensité dans la zone physiologique cible."
        ),
        metrics=(
            GoalMetricDefinition(
                key="time_in_heart_rate_target",
                label="Temps dans la zone cardiaque cible",
                importance=MetricImportance.PRIMARY,
                reason=(
                    "La maîtrise de l'intensité constitue "
                    "l'objectif principal d'une séance "
                    "d'endurance fondamentale."
                ),
            ),
            GoalMetricDefinition(
                key="time_in_pace_target",
                label="Temps dans l'allure cible",
                importance=MetricImportance.PRIMARY,
                reason=(
                    "L'allure complète l'analyse de "
                    "l'intensité lorsqu'une cible est prescrite."
                ),
            ),
            GoalMetricDefinition(
                key="duration",
                label="Durée",
                importance=MetricImportance.SECONDARY,
                reason=(
                    "La durée détermine le volume de travail "
                    "aérobie réellement accumulé."
                ),
            ),
            GoalMetricDefinition(
                key="distance",
                label="Distance",
                importance=MetricImportance.INFORMATIONAL,
                reason=(
                    "La distance décrit la séance mais ne doit "
                    "pas pousser l'athlète à augmenter "
                    "l'intensité pour atteindre un kilométrage."
                ),
            ),
            GoalMetricDefinition(
                key="elevation_gain",
                label="Dénivelé positif",
                importance=MetricImportance.INFORMATIONAL,
                reason=(
                    "Le dénivelé contextualise la charge "
                    "mécanique et l'allure."
                ),
            ),
            GoalMetricDefinition(
                key="training_load",
                label="Charge d'entraînement",
                importance=MetricImportance.INFORMATIONAL,
                reason=(
                    "La charge contextualise la séance mais "
                    "n'est pas l'objectif principal."
                ),
            ),
        ),
    )
