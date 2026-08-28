"""Objectif des séances fractionnées structurées."""

from __future__ import annotations

from .models import (
    GoalAnalysisPlan,
    GoalMetricDefinition,
    GoalType,
    MetricImportance,
)


def build_intervals_goal_plan(
) -> GoalAnalysisPlan:
    """Construit le plan d'analyse d'un fractionné."""

    return GoalAnalysisPlan(
        goal_type=GoalType.INTERVALS,
        objective=(
            "Réaliser les répétitions prescrites à "
            "l'intensité demandée, avec une récupération "
            "et une régularité compatibles avec le stimulus."
        ),
        metrics=(
            GoalMetricDefinition(
                key="work_duration",
                label="Allure / chrono des répétitions",
                importance=MetricImportance.PRIMARY,
                reason=(
                    "L'intensité des fractions détermine "
                    "directement le stimulus recherché. "
                    "Courir beaucoup trop vite n'est pas "
                    "plus conforme."
                ),
            ),
            GoalMetricDefinition(
                key="repetition_count",
                label="Nombre de répétitions",
                importance=MetricImportance.PRIMARY,
                reason=(
                    "Le nombre de fractions détermine le "
                    "volume de travail spécifique réalisé."
                ),
            ),
            GoalMetricDefinition(
                key="work_distance",
                label="Distance des répétitions",
                importance=MetricImportance.SECONDARY,
                reason=(
                    "La distance confirme que les fractions "
                    "réalisées correspondent bien au format "
                    "prescrit."
                ),
            ),
            GoalMetricDefinition(
                key="recovery_duration",
                label="Récupération",
                importance=MetricImportance.SECONDARY,
                reason=(
                    "La récupération influence la qualité "
                    "et la nature physiologique du stimulus."
                ),
            ),
            GoalMetricDefinition(
                key="repetition_regularity",
                label="Régularité",
                importance=MetricImportance.SECONDARY,
                reason=(
                    "La régularité permet de vérifier que "
                    "l'intensité reste maîtrisée sur la série."
                ),
            ),
            GoalMetricDefinition(
                key="repetition_degradation",
                label="Dégradation",
                importance=MetricImportance.SECONDARY,
                reason=(
                    "Une forte dégradation peut indiquer une "
                    "intensité initiale excessive ou une "
                    "difficulté à maintenir le stimulus."
                ),
            ),
            GoalMetricDefinition(
                key="average_heart_rate",
                label="Fréquence cardiaque",
                importance=MetricImportance.INFORMATIONAL,
                reason=(
                    "La fréquence cardiaque contextualise "
                    "l'effort mais son inertie limite son "
                    "utilité sur les fractions courtes."
                ),
            ),
        ),
    )
