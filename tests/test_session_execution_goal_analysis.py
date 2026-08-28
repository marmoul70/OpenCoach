from datetime import date

from opencoach.models import TrainingSession
from opencoach.training.session_execution.goal_analysis import (
    GoalType,
    MetricImportance,
    resolve_goal_analysis_plan,
)


def session(
    *,
    session_type="aerobic_easy",
    prescription=None,
):
    return TrainingSession(
        id=None,
        date=date(2026, 8, 28),
        type=session_type,
        sport_type="Run",
        title="Test",
        description="Test",
        duration_minutes=60,
        intensity="easy",
        prescription=(
            prescription
            if prescription is not None
            else {"version": 1}
        ),
    )


def test_endurance_prioritizes_zone_over_distance() -> None:
    result = resolve_goal_analysis_plan(
        session(
            prescription={
                "intensity": {
                    "targets": [
                        {
                            "reference": "heart_rate",
                            "minimum": 130,
                            "maximum": 150,
                        },
                    ],
                },
            }
        )
    )

    assert result.goal_type is GoalType.ENDURANCE

    metrics = {
        metric.key: metric
        for metric in result.metrics
    }

    assert (
        metrics[
            "time_in_heart_rate_target"
        ].importance
        is MetricImportance.PRIMARY
    )

    assert (
        metrics["duration"].importance
        is MetricImportance.SECONDARY
    )

    assert (
        metrics["distance"].importance
        is MetricImportance.INFORMATIONAL
    )


def test_intervals_prioritize_work_intensity() -> None:
    result = resolve_goal_analysis_plan(
        session(
            prescription={
                "work_structure": {
                    "type": "repeats",
                    "intervals": [
                        {
                            "repetitions": 7,
                            "work_distance_meters": 300,
                            "recovery_duration": 60,
                            "recovery_unit": "seconds",
                        },
                    ],
                },
            }
        )
    )

    assert result.goal_type is GoalType.INTERVALS

    metrics = {
        metric.key: metric
        for metric in result.metrics
    }

    assert (
        metrics["work_duration"].importance
        is MetricImportance.PRIMARY
    )

    assert (
        metrics["repetition_count"].importance
        is MetricImportance.PRIMARY
    )

    assert (
        metrics["recovery_duration"].importance
        is MetricImportance.SECONDARY
    )


def test_physiological_test_expects_vma_result() -> None:
    result = resolve_goal_analysis_plan(
        session(
            session_type="physiological_test",
        )
    )

    assert (
        result.goal_type
        is GoalType.PHYSIOLOGICAL_TEST
    )

    assert "vma_kmh" in (
        result.expected_derived_results
    )

    metrics = {
        metric.key: metric
        for metric in result.metrics
    }

    assert (
        metrics["duration"].importance
        is MetricImportance.PRIMARY
    )

    assert (
        metrics["distance"].importance
        is MetricImportance.PRIMARY
    )


def test_rest_has_no_execution_metrics() -> None:
    result = resolve_goal_analysis_plan(
        session(
            session_type="rest",
        )
    )

    assert result.goal_type is GoalType.REST
    assert result.metrics == ()


def test_generic_session_has_explicit_fallback() -> None:
    result = resolve_goal_analysis_plan(
        session()
    )

    assert result.goal_type is GoalType.GENERIC
