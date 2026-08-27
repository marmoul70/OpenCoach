from datetime import date, datetime
from uuid import uuid4

from opencoach.models import Activity, Race
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

class FakeRaceRepository:
    """Double du repository des courses."""

    def __init__(
        self,
        races: list[Race],
    ) -> None:
        self.races = races
        self.calls = []

    def list_races_between(
        self,
        athlete_profile_id,
        start_date,
        end_date,
    ):
        self.calls.append(
            (
                athlete_profile_id,
                start_date,
                end_date,
            )
        )

        return self.races

def create_activity(
    *,
    activity_id=None,
) -> Activity:
    return Activity(
        id=activity_id,
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
def create_race(
    *,
    activity_id=None,
) -> Race:
    return Race(
        id=uuid4(),
        date=date(
            2026,
            8,
            20,
        ),
        name="Course test",
        location="Jura",
        race_type="trail",
        priority="training",
        distance_km=30.0,
        elevation_gain_m=1500.0,
        status="completed",
        activity_id=activity_id,
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
        race_repository=FakeRaceRepository([]),
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
            date(2026, 8, 8),
            date(2026, 8, 21),
        ),
        (
            date(2026, 8, 1),
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

    assert snapshot.last_14_days is not None
    assert snapshot.last_21_days is not None

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
        race_repository=FakeRaceRepository([]),
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
def test_builds_race_activity_ids_from_historical_races() -> None:
    """Les compétitions liées sont identifiées dans le snapshot."""

    athlete_profile_id = uuid4()
    race_activity_id = uuid4()

    stats_service = (
        FakeTrainingStatsService()
    )

    activity_repository = (
        FakeActivityRepository(
            [
                create_activity(
                    activity_id=race_activity_id,
                ),
            ]
        )
    )

    race_repository = (
        FakeRaceRepository(
            [
                create_race(
                    activity_id=race_activity_id,
                ),
                create_race(
                    activity_id=None,
                ),
            ]
        )
    )

    service = TrainingHistorySnapshotService(
        training_stats_service=stats_service,
        activity_repository=activity_repository,
        race_repository=race_repository,
    )

    snapshot = service.build(
        athlete_profile_id,
        REFERENCE_DATE,
    )

    assert race_repository.calls == [
        (
            athlete_profile_id,
            date(2026, 5, 30),
            date(2026, 8, 21),
        )
    ]

    assert snapshot.race_activity_ids == frozenset(
        {
            race_activity_id,
        }
    )