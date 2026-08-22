from datetime import date, datetime
from uuid import uuid4

from opencoach.models import Activity
from opencoach.planning import (
    TrainingHistorySnapshotService,
)
from opencoach.training import TrainingStats


REFERENCE_DATE = date(
    2026,
    8,
    22,
)


class FakeTrainingStatsService:
    def __init__(self) -> None:
        self.calls = []

    def calculate(
        self,
        athlete_profile_id,
        start_date,
        end_date,
    ) -> TrainingStats:
        self.calls.append(
            (
                start_date,
                end_date,
            )
        )

        return TrainingStats(
            start_date=start_date,
            end_date=end_date,
            activities_count=1,
            manual_sessions_count=0,
            total_duration_minutes=60,
            total_distance_km=10.0,
            total_elevation_gain_m=200.0,
            measured_load=50.0,
            estimated_load=0.0,
        )


class FakeActivityRepository:
    def __init__(
        self,
        activities: list[Activity],
    ) -> None:
        self.activities = activities

        self.start_date = None
        self.end_date = None

    def list_activities_between(
        self,
        athlete_profile_id,
        start_date,
        end_date,
    ):
        self.start_date = start_date
        self.end_date = end_date

        return self.activities


def create_activity() -> Activity:
    return Activity(
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


def test_builds_expected_training_windows() -> None:
    stats_service = FakeTrainingStatsService()

    activity_repository = FakeActivityRepository(
        [
            create_activity(),
        ]
    )

    service = TrainingHistorySnapshotService(
        training_stats_service=stats_service,
        activity_repository=activity_repository,
    )

    snapshot = service.build(
        uuid4(),
        REFERENCE_DATE,
    )

    assert stats_service.calls == [
        (
            date(2026, 8, 15),
            date(2026, 8, 21),
        ),
        (
            date(2026, 7, 25),
            date(2026, 8, 21),
        ),
        (
            date(2026, 7, 11),
            date(2026, 8, 21),
        ),
        (
            date(2026, 5, 30),
            date(2026, 8, 21),
        ),
    ]

    assert snapshot.reference_date == (
        REFERENCE_DATE
    )

    assert len(
        snapshot.activities_84_days
    ) == 1


def test_loads_detailed_activities_for_84_days() -> None:
    stats_service = FakeTrainingStatsService()

    activity = create_activity()

    activity_repository = FakeActivityRepository(
        [
            activity,
        ]
    )

    service = TrainingHistorySnapshotService(
        training_stats_service=stats_service,
        activity_repository=activity_repository,
    )

    snapshot = service.build(
        uuid4(),
        REFERENCE_DATE,
    )

    assert activity_repository.start_date == (
        date(2026, 5, 30)
    )

    assert activity_repository.end_date == (
        date(2026, 8, 21)
    )

    assert snapshot.activities_84_days == (
        activity,
    )
