from datetime import date, datetime, timedelta

import pytest

from opencoach.models import Activity
from opencoach.planning.history.metrics import (
    calculate_training_history_metrics,
)
from opencoach.planning.history.training import (
    TrainingHistorySnapshot,
)
from opencoach.planning.physiology.training_load_baseline import (
    calculate_training_load_baseline,
)
from opencoach.training import TrainingStats


REFERENCE_DATE = date(
    2026,
    8,
    28,
)


def create_stats(
    *,
    days: int,
    duration_minutes: int,
    training_load: float,
    sessions_count: int,
) -> TrainingStats:
    return TrainingStats(
        start_date=(
            REFERENCE_DATE
            - timedelta(days=days)
        ),
        end_date=(
            REFERENCE_DATE
            - timedelta(days=1)
        ),
        activities_count=sessions_count,
        manual_sessions_count=0,
        total_duration_minutes=duration_minutes,
        total_distance_km=0.0,
        total_elevation_gain_m=0.0,
        measured_load=training_load,
        estimated_load=0.0,
    )


def create_activity(
    *,
    days_before_reference: int,
) -> Activity:
    activity_date = (
        REFERENCE_DATE
        - timedelta(
            days=days_before_reference
        )
    )

    return Activity(
        provider="test",
        provider_activity_id=(
            f"activity-{days_before_reference}"
        ),
        name="Test",
        sport_type="Run",
        start_at=datetime.combine(
            activity_date,
            datetime.min.time(),
        ),
        moving_time_seconds=3600,
        training_load=50.0,
    )


def create_snapshot(
    *,
    oldest_activity_days: int,
    stats_7: TrainingStats,
    stats_14: TrainingStats,
    stats_21: TrainingStats,
    stats_28: TrainingStats,
) -> TrainingHistorySnapshot:
    return TrainingHistorySnapshot(
        reference_date=REFERENCE_DATE,
        last_7_days=stats_7,
        last_28_days=stats_28,
        last_42_days=stats_28,
        last_84_days=stats_28,
        activities_84_days=(
            create_activity(
                days_before_reference=(
                    oldest_activity_days
                ),
            ),
        ),
        last_14_days=stats_14,
        last_21_days=stats_21,
    )


@pytest.mark.parametrize(
    (
        "oldest_activity_days",
        "expected_window_days",
        "expected_duration",
        "expected_load",
    ),
    [
        (
            6,
            7,
            210.0,
            210.0,
        ),
        (
            10,
            14,
            220.0,
            220.0,
        ),
        (
            18,
            21,
            230.0,
            230.0,
        ),
        (
            25,
            28,
            240.0,
            240.0,
        ),
        (
            60,
            28,
            240.0,
            240.0,
        ),
    ],
)
def test_adaptive_weekly_reference_uses_available_history_depth(
    oldest_activity_days: int,
    expected_window_days: int,
    expected_duration: float,
    expected_load: float,
) -> None:
    snapshot = create_snapshot(
        oldest_activity_days=(
            oldest_activity_days
        ),
        stats_7=create_stats(
            days=7,
            duration_minutes=210,
            training_load=210.0,
            sessions_count=3,
        ),
        stats_14=create_stats(
            days=14,
            duration_minutes=440,
            training_load=440.0,
            sessions_count=6,
        ),
        stats_21=create_stats(
            days=21,
            duration_minutes=690,
            training_load=690.0,
            sessions_count=9,
        ),
        stats_28=create_stats(
            days=28,
            duration_minutes=960,
            training_load=960.0,
            sessions_count=12,
        ),
    )

    metrics = (
        calculate_training_history_metrics(
            snapshot
        )
    )

    reference = (
        metrics.adaptive_weekly_reference
    )

    assert reference is not None

    assert (
        metrics.adaptive_window_days
        == expected_window_days
    )

    assert (
        reference.duration_minutes
        == expected_duration
    )

    assert (
        reference.training_load
        == expected_load
    )


def test_adaptive_reference_does_not_dilute_one_week_over_28_days() -> None:
    snapshot = create_snapshot(
        oldest_activity_days=6,
        stats_7=create_stats(
            days=7,
            duration_minutes=256,
            training_load=233.0,
            sessions_count=4,
        ),
        stats_14=create_stats(
            days=14,
            duration_minutes=256,
            training_load=233.0,
            sessions_count=4,
        ),
        stats_21=create_stats(
            days=21,
            duration_minutes=256,
            training_load=233.0,
            sessions_count=4,
        ),
        stats_28=create_stats(
            days=28,
            duration_minutes=256,
            training_load=233.0,
            sessions_count=4,
        ),
    )

    metrics = (
        calculate_training_history_metrics(
            snapshot
        )
    )

    reference = (
        metrics.adaptive_weekly_reference
    )

    assert reference is not None

    assert metrics.adaptive_window_days == 7

    assert (
        reference.duration_minutes
        == 256.0
    )

    assert (
        reference.training_load
        == 233.0
    )

    # La moyenne 28 jours historique reste disponible
    # pour les autres indicateurs, mais elle ne doit pas
    # devenir la baseline hebdomadaire.
    assert (
        metrics.last_28_days.duration_minutes
        == 64.0
    )

    assert (
        metrics.last_28_days.training_load
        == 58.25
    )


def test_training_load_baseline_uses_adaptive_reference() -> None:
    snapshot = create_snapshot(
        oldest_activity_days=6,
        stats_7=create_stats(
            days=7,
            duration_minutes=256,
            training_load=233.0,
            sessions_count=4,
        ),
        stats_14=create_stats(
            days=14,
            duration_minutes=256,
            training_load=233.0,
            sessions_count=4,
        ),
        stats_21=create_stats(
            days=21,
            duration_minutes=256,
            training_load=233.0,
            sessions_count=4,
        ),
        stats_28=create_stats(
            days=28,
            duration_minutes=256,
            training_load=233.0,
            sessions_count=4,
        ),
    )

    metrics = (
        calculate_training_history_metrics(
            snapshot
        )
    )

    baseline = (
        calculate_training_load_baseline(
            metrics
        )
    )

    assert baseline.baseline_load == 233.0

    # Une seule semaine disponible sur les quatre
    # nécessaires à une référence mature.
    assert baseline.confidence == 0.25
