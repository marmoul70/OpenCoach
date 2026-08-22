from datetime import date, datetime

from opencoach.models import Activity
from opencoach.planning import (
    TrainingHistorySnapshot,
    calculate_training_history_metrics,
)
from opencoach.training import TrainingStats


def create_stats(
    *,
    days: int,
    sessions: int,
    duration_minutes: int,
    distance_km: float,
    elevation_gain_m: float,
    load: float,
) -> TrainingStats:
    return TrainingStats(
        start_date=date(
            2026,
            8,
            1,
        ),
        end_date=date(
            2026,
            8,
            21,
        ),
        activities_count=sessions,
        manual_sessions_count=0,
        total_duration_minutes=duration_minutes,
        total_distance_km=distance_km,
        total_elevation_gain_m=elevation_gain_m,
        measured_load=load,
        estimated_load=0.0,
    )


def create_activity(
    *,
    name: str,
    duration_minutes: int | None,
    distance_km: float | None,
    elevation_gain_m: float | None,
) -> Activity:
    return Activity(
        provider="intervals",
        provider_activity_id=name,
        name=name,
        sport_type="Run",
        start_at=datetime(
            2026,
            8,
            20,
            10,
            0,
        ),
        moving_time_seconds=(
            duration_minutes * 60
            if duration_minutes is not None
            else None
        ),
        distance_m=(
            distance_km * 1000
            if distance_km is not None
            else None
        ),
        elevation_gain_m=elevation_gain_m,
    )


def create_snapshot(
    activities=(),
) -> TrainingHistorySnapshot:
    return TrainingHistorySnapshot(
        reference_date=date(
            2026,
            8,
            22,
        ),
        last_7_days=create_stats(
            days=7,
            sessions=4,
            duration_minutes=300,
            distance_km=45.0,
            elevation_gain_m=1200.0,
            load=280.0,
        ),
        last_28_days=create_stats(
            days=28,
            sessions=16,
            duration_minutes=1200,
            distance_km=180.0,
            elevation_gain_m=4800.0,
            load=1120.0,
        ),
        last_42_days=create_stats(
            days=42,
            sessions=24,
            duration_minutes=1800,
            distance_km=270.0,
            elevation_gain_m=7200.0,
            load=1680.0,
        ),
        last_84_days=create_stats(
            days=84,
            sessions=48,
            duration_minutes=3600,
            distance_km=540.0,
            elevation_gain_m=14400.0,
            load=3360.0,
        ),
        activities_84_days=tuple(
            activities
        ),
    )


def test_calculates_weekly_averages() -> None:
    metrics = calculate_training_history_metrics(
        create_snapshot()
    )

    assert metrics.last_7_days.sessions == 4.0
    assert metrics.last_7_days.duration_minutes == 300.0
    assert metrics.last_7_days.distance_km == 45.0
    assert metrics.last_7_days.elevation_gain_m == 1200.0
    assert metrics.last_7_days.training_load == 280.0

    assert metrics.last_28_days.sessions == 4.0
    assert metrics.last_84_days.sessions == 4.0


def test_finds_longest_activity() -> None:
    short = create_activity(
        name="Short",
        duration_minutes=60,
        distance_km=10.0,
        elevation_gain_m=200.0,
    )

    long = create_activity(
        name="Long",
        duration_minutes=150,
        distance_km=25.0,
        elevation_gain_m=900.0,
    )

    metrics = calculate_training_history_metrics(
        create_snapshot(
            activities=(
                short,
                long,
            )
        )
    )

    assert metrics.longest_activity is long
    assert metrics.longest_duration_minutes == 150.0
    assert metrics.longest_distance_km == 25.0


def test_finds_highest_elevation_activity() -> None:
    first = create_activity(
        name="First",
        duration_minutes=120,
        distance_km=20.0,
        elevation_gain_m=700.0,
    )

    second = create_activity(
        name="Second",
        duration_minutes=90,
        distance_km=14.0,
        elevation_gain_m=1400.0,
    )

    metrics = calculate_training_history_metrics(
        create_snapshot(
            activities=(
                first,
                second,
            )
        )
    )

    assert (
        metrics.highest_elevation_activity
        is second
    )

    assert (
        metrics.highest_elevation_gain_m
        == 1400.0
    )


def test_handles_missing_activity_metrics() -> None:
    activity = create_activity(
        name="Incomplete",
        duration_minutes=None,
        distance_km=None,
        elevation_gain_m=None,
    )

    metrics = calculate_training_history_metrics(
        create_snapshot(
            activities=(
                activity,
            )
        )
    )

    assert metrics.longest_activity is None
    assert metrics.longest_duration_minutes is None
    assert metrics.longest_distance_km is None

    assert (
        metrics.highest_elevation_activity
        is None
    )

    assert (
        metrics.highest_elevation_gain_m
        is None
    )
