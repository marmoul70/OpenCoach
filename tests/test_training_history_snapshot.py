from datetime import date, datetime, timedelta

from opencoach.models import Activity
from opencoach.planning import (
    TrainingHistorySnapshot,
)
from opencoach.training import TrainingStats


def create_stats(
    *,
    days: int,
    sessions: int,
) -> TrainingStats:
    end_date = date(
        2026,
        8,
        21,
    )

    start_date = (
        end_date
        - timedelta(days=days - 1)
    )

    return TrainingStats(
        start_date=start_date,
        end_date=end_date,
        activities_count=sessions,
        manual_sessions_count=0,
        total_duration_minutes=300,
        total_distance_km=40.0,
        total_elevation_gain_m=1000.0,
        measured_load=200.0,
        estimated_load=0.0,
    )


def test_snapshot_reports_training_history() -> None:
    activity = Activity(
        provider="intervals",
        provider_activity_id="test",
        name="Trail",
        sport_type="Run",
        start_at=datetime(
            2026,
            8,
            20,
            10,
            0,
        ),
    )

    snapshot = TrainingHistorySnapshot(
        reference_date=date(
            2026,
            8,
            22,
        ),
        last_7_days=create_stats(
            days=7,
            sessions=2,
        ),
        last_28_days=create_stats(
            days=28,
            sessions=8,
        ),
        last_42_days=create_stats(
            days=42,
            sessions=12,
        ),
        last_84_days=create_stats(
            days=84,
            sessions=24,
        ),
        activities_84_days=(
            activity,
        ),
    )

    assert snapshot.has_training_history is True


def test_snapshot_detects_empty_history() -> None:
    empty = create_stats(
        days=84,
        sessions=0,
    )

    snapshot = TrainingHistorySnapshot(
        reference_date=date(
            2026,
            8,
            22,
        ),
        last_7_days=empty,
        last_28_days=empty,
        last_42_days=empty,
        last_84_days=empty,
        activities_84_days=(),
    )

    assert snapshot.has_training_history is False
