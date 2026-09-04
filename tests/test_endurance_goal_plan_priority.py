"""Tests de priorité métier du débrief d'endurance fondamentale."""

from opencoach.training.session_execution.goal_analysis.endurance import (
    build_endurance_goal_plan,
)
from opencoach.training.session_execution.goal_analysis.models import (
    MetricImportance,
)


def test_endurance_uses_hr_as_primary_and_pace_as_informational() -> None:
    """La FC pilote l'EF ; l'allure contextualise sans sanctionner."""
    plan = build_endurance_goal_plan()

    metrics = {
        metric.key: metric
        for metric in plan.metrics
    }

    assert (
        metrics["time_in_heart_rate_target"].importance
        is MetricImportance.PRIMARY
    )

    assert (
        metrics["time_in_pace_target"].importance
        is MetricImportance.INFORMATIONAL
    )

    assert (
        metrics["duration"].importance
        is MetricImportance.SECONDARY
    )
