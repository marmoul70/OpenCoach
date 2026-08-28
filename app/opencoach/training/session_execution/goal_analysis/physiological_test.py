"""Objectif des séances de test physiologique."""

from __future__ import annotations

from opencoach.models import TrainingSession

from .models import (
    GoalAnalysisPlan,
    GoalMetricDefinition,
    GoalType,
    MetricImportance,
)


def build_physiological_test_goal_plan(
    session: TrainingSession,
) -> GoalAnalysisPlan:
    """Construit le plan d'analyse d'un test physiologique."""

    return GoalAnalysisPlan(
        goal_type=GoalType.PHYSIOLOGICAL_TEST,
        objective=(
            "Vérifier que le protocole du test a été "
            "correctement exécuté puis produire les "
            "paramètres physiologiques dérivés."
        ),
        metrics=(
            GoalMetricDefinition(
                key="duration",
                label="Durée du protocole",
                importance=MetricImportance.PRIMARY,
                reason=(
                    "La durée du protocole doit être "
                    "respectée pour rendre le résultat valide."
                ),
            ),
            GoalMetricDefinition(
                key="distance",
                label="Distance du test",
                importance=MetricImportance.PRIMARY,
                reason=(
                    "La distance constitue une donnée "
                    "principale pour les tests de terrain "
                    "comme le demi-Cooper."
                ),
            ),
            GoalMetricDefinition(
                key="average_speed",
                label="Vitesse réalisée",
                importance=MetricImportance.SECONDARY,
                reason=(
                    "La vitesse aide à qualifier la "
                    "performance obtenue pendant le test."
                ),
            ),
            GoalMetricDefinition(
                key="average_heart_rate",
                label="Réponse cardiaque",
                importance=MetricImportance.INFORMATIONAL,
                reason=(
                    "La fréquence cardiaque apporte un "
                    "contexte sur l'intensité du test."
                ),
            ),
        ),
        expected_derived_results=(
            "vma_kmh",
        ),
    )
