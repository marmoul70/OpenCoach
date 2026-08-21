from datetime import (
    date,
    datetime,
)
from uuid import UUID, uuid4

from opencoach.models import (
    Activity,
    TrainingSession,
)
from opencoach.training import (
    TrainingStatsService,
)


START_DATE = date(
    2026,
    8,
    20,
)

END_DATE = date(
    2026,
    8,
    20,
)


class FakeActivityRepository:
    def __init__(
        self,
        activities: list[Activity],
    ) -> None:
        self.activities = activities
        self.calls = []

    def list_activities_between(
        self,
        athlete_profile_id: UUID,
        start_date: date,
        end_date: date,
    ) -> list[Activity]:
        self.calls.append(
            (
                athlete_profile_id,
                start_date,
                end_date,
            )
        )

        return self.activities


class FakeTrainingSessionRepository:
    def __init__(
        self,
        sessions: list[TrainingSession],
    ) -> None:
        self.sessions = sessions
        self.calls = []

    def list_sessions_between(
        self,
        athlete_profile_id: UUID,
        start_date: date,
        end_date: date,
    ) -> list[TrainingSession]:
        self.calls.append(
            (
                athlete_profile_id,
                start_date,
                end_date,
            )
        )

        return self.sessions


def test_training_stats_use_linked_activity_as_actual() -> None:
    activity_id = uuid4()

    activity = Activity(
        id=activity_id,
        provider="intervals",
        provider_activity_id="i177856854",
        name="Morning Course à pied",
        sport_type="Run",
        start_at=datetime(
            2026,
            8,
            20,
            8,
            43,
            14,
        ),
        distance_m=6340.0,
        moving_time_seconds=2171,
        elapsed_time_seconds=2561,
        elevation_gain_m=120.0,
        training_load=31.0,
    )

    session = TrainingSession(
        id=uuid4(),
        date=START_DATE,
        type="long",
        sport_type="Run",
        title="Sortie longue trail",
        description="18 km prévus.",
        duration_minutes=135,
        distance_km=18.0,
        elevation_gain_m=500.0,
        intensity="moderate",
        heart_rate_zone="Z2",
        status="completed",
        activity_id=activity_id,
    )

    service = TrainingStatsService(
        FakeActivityRepository(
            [activity]
        ),
        FakeTrainingSessionRepository(
            [session]
        ),
    )

    result = service.calculate(
        uuid4(),
        START_DATE,
        END_DATE,
    )

    assert result.activities_count == 1
    assert result.manual_sessions_count == 0

    assert result.sessions_count == 1

    assert result.total_distance_km == 6.34
    assert result.total_duration_minutes == 36
    assert result.total_elevation_gain_m == 120.0

    assert result.measured_load == 31.0
    assert result.estimated_load == 0.0
    assert result.total_load == 31.0

def test_training_stats_use_completed_manual_session_without_activity() -> None:
    session = TrainingSession(
        id=uuid4(),
        date=START_DATE,
        type="easy",
        sport_type="Run",
        title="Footing manuel",
        description="Séance saisie manuellement.",
        duration_minutes=45,
        distance_km=8.0,
        elevation_gain_m=100.0,
        intensity="easy",
        heart_rate_zone="Z2",
        status="completed",
        activity_id=None,
    )

    service = TrainingStatsService(
        FakeActivityRepository([]),
        FakeTrainingSessionRepository(
            [session]
        ),
    )

    result = service.calculate(
        uuid4(),
        START_DATE,
        END_DATE,
    )

    assert result.activities_count == 0
    assert result.manual_sessions_count == 1

    assert result.sessions_count == 1

    assert result.total_distance_km == 8.0
    assert result.total_duration_minutes == 45
    assert result.total_elevation_gain_m == 100.0

    assert result.measured_load == 0.0
    assert result.estimated_load > 0.0