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
    assert result.duration_data_count == 1
    assert result.distance_data_count == 1
    assert result.elevation_data_count == 1
    assert result.measured_load_data_count == 1

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
    assert result.duration_data_count == 1
    assert result.distance_data_count == 1
    assert result.elevation_data_count == 1
    assert result.measured_load_data_count == 0
    assert result.estimated_load_data_count == 1


def test_training_stats_do_not_count_manual_session_without_duration_as_estimated_load():
    session = TrainingSession(
        id=uuid4(),
        date=START_DATE,
        type="easy",
        sport_type="Run",
        title="Séance manuelle incomplète",
        description="Durée non renseignée.",
        duration_minutes=0,
        distance_km=None,
        elevation_gain_m=None,
        intensity="easy",
        heart_rate_zone=None,
        status="completed",
        activity_id=None,
    )

    service = TrainingStatsService(
        FakeActivityRepository([]),
        FakeTrainingSessionRepository([session]),
    )

    result = service.calculate(uuid4(), START_DATE, END_DATE)

    assert result.sessions_count == 1
    assert result.manual_sessions_count == 1
    assert result.estimated_load == 0.0
    assert result.estimated_load_data_count == 0



def test_training_stats_exposes_shared_metric_coverage_statuses() -> None:
    from opencoach.training import TrainingStats

    stats = TrainingStats(
        start_date=START_DATE,
        end_date=END_DATE,
        activities_count=2,
        manual_sessions_count=1,
        total_duration_minutes=120,
        total_distance_km=20.0,
        total_elevation_gain_m=300.0,
        measured_load=40.0,
        estimated_load=20.0,
    )

    assert stats.coverage(0) == {
        "available_sessions": 0,
        "total_sessions": 3,
        "status": "unavailable",
    }
    assert stats.coverage(2) == {
        "available_sessions": 2,
        "total_sessions": 3,
        "status": "partial",
    }
    assert stats.coverage(3) == {
        "available_sessions": 3,
        "total_sessions": 3,
        "status": "complete",
    }

    empty = TrainingStats(
        start_date=START_DATE,
        end_date=END_DATE,
        activities_count=0,
        manual_sessions_count=0,
        total_duration_minutes=0,
        total_distance_km=0.0,
        total_elevation_gain_m=0.0,
        measured_load=0.0,
        estimated_load=0.0,
    )
    assert empty.coverage(0)["status"] == "no_sessions"



def test_training_stats_compare_to_uses_shared_coverage_and_suppresses_unreliable_deltas() -> None:
    from opencoach.training import TrainingStats

    current = TrainingStats(
        start_date=START_DATE,
        end_date=END_DATE,
        activities_count=2,
        manual_sessions_count=0,
        total_duration_minutes=120,
        total_distance_km=20.0,
        total_elevation_gain_m=400.0,
        measured_load=80.0,
        estimated_load=0.0,
        duration_data_count=2,
        distance_data_count=1,
        elevation_data_count=2,
        measured_load_data_count=2,
    )
    previous = TrainingStats(
        start_date=START_DATE,
        end_date=END_DATE,
        activities_count=2,
        manual_sessions_count=0,
        total_duration_minutes=100,
        total_distance_km=18.0,
        total_elevation_gain_m=350.0,
        measured_load=70.0,
        estimated_load=0.0,
        duration_data_count=2,
        distance_data_count=2,
        elevation_data_count=2,
        measured_load_data_count=2,
    )

    result = current.compare_to(previous)
    assert result["metrics"]["duration_minutes"]["trend"]["delta"] == 20
    assert result["metrics"]["distance_km"]["current_period"]["value"] is None
    assert result["metrics"]["distance_km"]["current_period"]["partial_observed_value"] == 20.0
    assert result["metrics"]["distance_km"]["trend"] == {
        "delta": None,
        "percent_delta": None,
        "status": "insufficient_coverage",
    }
    assert len(result["warnings"]) == 1
