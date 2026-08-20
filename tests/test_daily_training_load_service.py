from datetime import date, datetime, timezone
from uuid import UUID, uuid4

from opencoach.database.repositories import (
    ActivityRepository,
    TrainingSessionRepository,
)
from opencoach.models import (
    Activity,
    TrainingSession,
)
from opencoach.training import (
    DailyTrainingLoadService,
)


class FakeActivityRepository(
    ActivityRepository,
):
    def __init__(
        self,
        activities: list[Activity],
    ) -> None:
        self.activities = activities

    def save_activity(
        self,
        athlete_profile_id: UUID,
        activity: Activity,
    ) -> None:
        self.activities.append(
            activity,
        )

    def list_activities(
        self,
        athlete_profile_id: UUID,
    ) -> list[Activity]:
        return self.activities

    def list_activities_between(
        self,
        athlete_profile_id: UUID,
        start_date: date,
        end_date: date,
    ) -> list[Activity]:
        return self.activities


class FakeTrainingSessionRepository(
    TrainingSessionRepository,
):
    def __init__(
        self,
        sessions: list[TrainingSession],
    ) -> None:
        self.sessions = sessions

    def save_session(
        self,
        athlete_profile_id: UUID,
        session: TrainingSession,
    ) -> TrainingSession:
        self.sessions.append(
            session,
        )

        return session

    def get_session(
        self,
        athlete_profile_id: UUID,
        session_id: UUID,
    ) -> TrainingSession | None:
        for session in self.sessions:
            if session.id == session_id:
                return session

        return None

    def list_sessions_between(
        self,
        athlete_profile_id: UUID,
        start_date: date,
        end_date: date,
    ) -> list[TrainingSession]:
        return self.sessions

    def update_status(
        self,
        athlete_profile_id: UUID,
        session_id: UUID,
        status: str,
    ) -> TrainingSession:
        session = self.get_session(
            athlete_profile_id,
            session_id,
        )

        if session is None:
            raise RuntimeError(
                "Session introuvable.",
            )

        session.status = status

        return session

    def link_activity(
        self,
        athlete_profile_id: UUID,
        session_id: UUID,
        activity_id: UUID | None,
    ) -> TrainingSession:
        session = self.get_session(
            athlete_profile_id,
            session_id,
        )

        if session is None:
            raise RuntimeError(
                "Session introuvable.",
            )

        session.activity_id = (
            activity_id
        )

        return session

    def list_candidate_activities_for_date(
        self,
        athlete_profile_id: UUID,
        session_date: date,
    ) -> list[Activity]:
        return []

    def list_unlinked_activities_for_date(
        self,
        athlete_profile_id: UUID,
        session_date: date,
    ) -> list[Activity]:
        return []


def create_activity(
    *,
    activity_id: UUID | None = None,
    sport_type: str = "Run",
    moving_time_seconds: int | None = 3600,
    elapsed_time_seconds: int | None = None,
    distance_m: float | None = 10000.0,
    elevation_gain_m: float | None = 200.0,
    training_load: float | None = 50.0,
) -> Activity:
    return Activity(
        id=activity_id,
        provider="intervals",
        provider_activity_id=(
            f"activity-{uuid4()}"
        ),
        name="Activité test",
        sport_type=sport_type,
        start_at=datetime(
            2026,
            8,
            20,
            7,
            0,
            tzinfo=timezone.utc,
        ),
        moving_time_seconds=(
            moving_time_seconds
        ),
        elapsed_time_seconds=(
            elapsed_time_seconds
        ),
        distance_m=distance_m,
        elevation_gain_m=(
            elevation_gain_m
        ),
        training_load=training_load,
    )


def create_training_session(
    *,
    session_id: UUID | None = None,
    session_type: str = "supplementary",
    sport_type: str = "StrengthTraining",
    duration_minutes: int = 40,
    distance_km: float | None = None,
    elevation_gain_m: float | None = None,
    status: str = "completed",
    activity_id: UUID | None = None,
) -> TrainingSession:
    return TrainingSession(
        id=session_id or uuid4(),
        date=date(
            2026,
            8,
            20,
        ),
        type=session_type,
        sport_type=sport_type,
        title="Séance test",
        description="",
        duration_minutes=(
            duration_minutes
        ),
        distance_km=distance_km,
        elevation_gain_m=(
            elevation_gain_m
        ),
        intensity="Facile",
        heart_rate_zone="Z1",
        status=status,
        activity_id=activity_id,
    )


def create_service(
    *,
    activities: list[Activity] | None = None,
    sessions: list[TrainingSession] | None = None,
) -> DailyTrainingLoadService:
    return DailyTrainingLoadService(
        activity_repository=(
            FakeActivityRepository(
                activities or [],
            )
        ),
        training_session_repository=(
            FakeTrainingSessionRepository(
                sessions or [],
            )
        ),
    )


def test_daily_training_load_empty_day() -> None:
    service = create_service()

    result = service.calculate(
        uuid4(),
        date(
            2026,
            8,
            20,
        ),
    )

    assert result.activities_count == 0
    assert result.manual_sessions_count == 0
    assert result.sessions_count == 0

    assert result.total_duration_minutes == 0
    assert result.total_distance_km == 0.0
    assert result.total_elevation_gain_m == 0.0

    assert result.measured_load == 0.0
    assert result.estimated_load == 0.0
    assert result.total_load == 0.0
    assert result.sport_types == ()

    assert result.has_training is False


def test_daily_training_load_aggregates_activities() -> None:
    service = create_service(
        activities=[
            create_activity(
                sport_type="Run",
                moving_time_seconds=3600,
                distance_m=10000.0,
                elevation_gain_m=200.0,
                training_load=50.0,
            ),
            create_activity(
                sport_type="Swim",
                moving_time_seconds=1800,
                distance_m=1200.0,
                elevation_gain_m=None,
                training_load=25.0,
            ),
        ],
    )

    result = service.calculate(
        uuid4(),
        date(
            2026,
            8,
            20,
        ),
    )

    assert result.activities_count == 2
    assert result.manual_sessions_count == 0
    assert result.sessions_count == 2

    assert result.total_duration_minutes == 90
    assert result.total_distance_km == 11.2
    assert result.total_elevation_gain_m == 200.0

    assert result.measured_load == 75.0
    assert result.estimated_load == 0.0
    assert result.total_load == 75.0

    assert result.sport_types == (
        "Run",
        "Swim",
    )

    assert result.has_training is True


def test_daily_training_load_adds_manual_completed_session() -> None:
    service = create_service(
        activities=[
            create_activity(
                moving_time_seconds=3600,
                distance_m=10000.0,
                training_load=50.0,
            ),
        ],
        sessions=[
            create_training_session(
                duration_minutes=40,
                sport_type="StrengthTraining",
                elevation_gain_m=20.0,
            ),
        ],
    )

    result = service.calculate(
        uuid4(),
        date(
            2026,
            8,
            20,
        ),
    )

    assert result.activities_count == 1
    assert result.manual_sessions_count == 1
    assert result.sessions_count == 2

    assert result.total_duration_minutes == 100
    assert result.total_distance_km == 10.0
    assert result.total_elevation_gain_m == 220.0

    # Pour l'instant, seule la charge mesurée
    # des activités contribue à training_load.
    assert result.measured_load == 50.0
    assert result.estimated_load == 18.0
    assert result.total_load == 68.0

    assert result.sport_types == (
        "Run",
        "StrengthTraining",
    )


def test_daily_training_load_does_not_double_count_linked_session() -> None:
    activity_id = uuid4()

    service = create_service(
        activities=[
            create_activity(
                activity_id=activity_id,
                moving_time_seconds=3600,
                distance_m=10000.0,
                training_load=50.0,
            ),
        ],
        sessions=[
            create_training_session(
                duration_minutes=60,
                distance_km=10.0,
                activity_id=activity_id,
            ),
        ],
    )

    result = service.calculate(
        uuid4(),
        date(
            2026,
            8,
            20,
        ),
    )

    assert result.activities_count == 1
    assert result.manual_sessions_count == 0
    assert result.sessions_count == 1

    assert result.total_duration_minutes == 60
    assert result.total_distance_km == 10.0

    assert result.measured_load == 50.0
    assert result.estimated_load == 0.0
    assert result.total_load == 50.0


def test_daily_training_load_ignores_planned_session() -> None:
    service = create_service(
        sessions=[
            create_training_session(
                status="planned",
            ),
        ],
    )

    result = service.calculate(
        uuid4(),
        date(
            2026,
            8,
            20,
        ),
    )

    assert result.sessions_count == 0
    assert result.has_training is False


def test_daily_training_load_ignores_skipped_session() -> None:
    service = create_service(
        sessions=[
            create_training_session(
                status="skipped",
            ),
        ],
    )

    result = service.calculate(
        uuid4(),
        date(
            2026,
            8,
            20,
        ),
    )

    assert result.sessions_count == 0
    assert result.has_training is False


def test_daily_training_load_ignores_rest_session() -> None:
    service = create_service(
        sessions=[
            create_training_session(
                session_type="rest",
                duration_minutes=0,
            ),
        ],
    )

    result = service.calculate(
        uuid4(),
        date(
            2026,
            8,
            20,
        ),
    )

    assert result.sessions_count == 0
    assert result.has_training is False


def test_daily_training_load_uses_elapsed_time_as_fallback() -> None:
    service = create_service(
        activities=[
            create_activity(
                moving_time_seconds=None,
                elapsed_time_seconds=2700,
            ),
        ],
    )

    result = service.calculate(
        uuid4(),
        date(
            2026,
            8,
            20,
        ),
    )

    assert result.total_duration_minutes == 45


def test_daily_training_load_handles_missing_activity_metrics() -> None:
    service = create_service(
        activities=[
            create_activity(
                moving_time_seconds=None,
                elapsed_time_seconds=None,
                distance_m=None,
                elevation_gain_m=None,
                training_load=None,
            ),
        ],
    )

    result = service.calculate(
        uuid4(),
        date(
            2026,
            8,
            20,
        ),
    )

    assert result.activities_count == 1
    assert result.sessions_count == 1

    assert result.total_duration_minutes == 0
    assert result.total_distance_km == 0.0
    assert result.total_elevation_gain_m == 0.0

    assert result.measured_load == 0.0
    assert result.estimated_load == 0.0
    assert result.total_load == 0.0
