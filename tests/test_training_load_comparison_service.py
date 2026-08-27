from datetime import date
from uuid import UUID, uuid4

import pytest

from opencoach.training.load_estimation import (
    estimate_prescribed_load,
)

from opencoach.database.repositories import (
    TrainingSessionRepository,
)
from opencoach.models import (
    Activity,
    TrainingSession,
)
from opencoach.training import (
    DailyTrainingLoad,
    TrainingLoadComparisonService,
)


TARGET_DATE = date(
    2026,
    8,
    20,
)


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

        session.activity_id = activity_id

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

    def delete_session(
        self,
        session_id,
    ) -> None:
        self.sessions = [
            session
            for session in self.sessions
            if session.id != session_id
        ]


class FakeDailyTrainingLoadService:
    def __init__(
        self,
        result: DailyTrainingLoad,
    ) -> None:
        self.result = result

    def calculate(
        self,
        athlete_profile_id: UUID,
        target_date: date,
    ) -> DailyTrainingLoad:
        return self.result


def create_session(
    *,
    session_type: str = "easy",
    status: str = "planned",
    duration_minutes: int = 60,
    intensity: str = "easy",
) -> TrainingSession:
    return TrainingSession(
        id=uuid4(),
        date=TARGET_DATE,
        type=session_type,
        sport_type="Run",
        title="Séance test",
        description="",
        duration_minutes=duration_minutes,
        distance_km=10.0,
        elevation_gain_m=100.0,
        intensity=intensity,
        heart_rate_zone="Z2",
        status=status,
        activity_id=None,
    )


def create_actual(
    *,
    duration_minutes: int,
    measured_load: float,
    estimated_load: float = 0.0,
    activities_count: int = 1,
    manual_sessions_count: int = 0,
) -> DailyTrainingLoad:
    return DailyTrainingLoad(
        date=TARGET_DATE,
        activities_count=activities_count,
        manual_sessions_count=(
            manual_sessions_count
        ),
        total_duration_minutes=(
            duration_minutes
        ),
        total_distance_km=10.0,
        total_elevation_gain_m=100.0,
        measured_load=measured_load,
        estimated_load=estimated_load,
        sport_types=("Run",),
    )


def create_service(
    *,
    sessions: list[TrainingSession],
    actual: DailyTrainingLoad,
) -> TrainingLoadComparisonService:
    return TrainingLoadComparisonService(
        training_session_repository=(
            FakeTrainingSessionRepository(
                sessions,
            )
        ),
        daily_training_load_service=(
            FakeDailyTrainingLoadService(
                actual,
            )
        ),
    )


def test_comparison_on_plan() -> None:
    service = create_service(
        sessions=[
            create_session(
                duration_minutes=60,
                intensity="easy",
            ),
        ],
        actual=create_actual(
            duration_minutes=60,
            measured_load=27.0,
        ),
    )

    result = service.calculate(
        uuid4(),
        TARGET_DATE,
    )

    assert result.planned_load == 27.0
    assert result.actual_load == 27.0
    assert result.status == "on_plan"


def test_comparison_detects_extra_load() -> None:
    service = create_service(
        sessions=[
            create_session(
                duration_minutes=60,
                intensity="easy",
            ),
            create_session(
                session_type="supplementary",
                status="completed",
                duration_minutes=40,
                intensity="easy",
            ),
        ],
        actual=create_actual(
            duration_minutes=100,
            measured_load=27.0,
            estimated_load=18.0,
            activities_count=1,
            manual_sessions_count=1,
        ),
    )

    result = service.calculate(
        uuid4(),
        TARGET_DATE,
    )

    assert result.planned_load == 27.0
    assert result.actual_load == 45.0
    assert result.load_delta == 18.0

    assert (
        result.duration_delta_minutes
        == 40
    )

    assert result.status == "above_plan"


def test_comparison_detects_broken_rest() -> None:
    service = create_service(
        sessions=[
            create_session(
                session_type="rest",
                status="planned",
                duration_minutes=0,
                intensity="very_easy",
            ),
        ],
        actual=create_actual(
            duration_minutes=55,
            measured_load=25.0,
            activities_count=2,
        ),
    )

    result = service.calculate(
        uuid4(),
        TARGET_DATE,
    )

    assert result.planned_load == 0.0
    assert result.actual_load == 25.0
    assert result.status == "rest_broken"


def test_comparison_detects_respected_rest() -> None:
    service = create_service(
        sessions=[
            create_session(
                session_type="rest",
                status="planned",
                duration_minutes=0,
                intensity="very_easy",
            ),
        ],
        actual=create_actual(
            duration_minutes=0,
            measured_load=0.0,
            activities_count=0,
        ),
    )

    result = service.calculate(
        uuid4(),
        TARGET_DATE,
    )

    assert result.planned_load == 0.0
    assert result.actual_load == 0.0

    assert (
        result.status
        == "rest_respected"
    )


def test_comparison_uses_completed_coach_session_as_reference() -> None:
    service = create_service(
        sessions=[
            create_session(
                status="completed",
                duration_minutes=60,
                intensity="easy",
            ),
        ],
        actual=create_actual(
            duration_minutes=60,
            measured_load=27.0,
        ),
    )

    result = service.calculate(
        uuid4(),
        TARGET_DATE,
    )

    assert result.planned_load == 27.0
    assert result.actual_load == 27.0

    assert result.status == "on_plan"


def test_comparison_ignores_supplementary_session_as_reference() -> None:
    service = create_service(
        sessions=[
            create_session(
                session_type="rest",
                duration_minutes=0,
                intensity="very_easy",
            ),
            create_session(
                session_type="supplementary",
                status="completed",
                duration_minutes=40,
                intensity="easy",
            ),
        ],
        actual=create_actual(
            duration_minutes=40,
            measured_load=0.0,
            estimated_load=18.0,
            activities_count=0,
            manual_sessions_count=1,
        ),
    )

    result = service.calculate(
        uuid4(),
        TARGET_DATE,
    )

    assert result.planned_load == 0.0
    assert result.actual_load == 18.0

    assert result.status == "rest_broken"


def test_comparison_aggregates_multiple_coach_sessions() -> None:
    first = create_session(
        duration_minutes=45,
    )

    second = create_session(
        duration_minutes=15,
        status="completed",
    )

    service = create_service(
        sessions=[
            first,
            second,
        ],
        actual=create_actual(
            duration_minutes=60,
            measured_load=27.0,
        ),
    )

    result = service.calculate(
        uuid4(),
        TARGET_DATE,
    )

    assert (
        result.planned_duration_minutes
        == 60
    )

    assert (
        result.planned_sessions_count
        == 2
    )

    assert (
        result.planned_load
        == (
            estimate_prescribed_load(
                first,
            )
            + estimate_prescribed_load(
                second,
            )
        )
    )


def test_comparison_without_prescription_with_activity_is_unplanned() -> None:
    service = create_service(
        sessions=[],
        actual=create_actual(
            duration_minutes=55,
            measured_load=25.0,
            activities_count=1,
        ),
    )

    result = service.calculate(
        uuid4(),
        TARGET_DATE,
    )

    assert result.planned_load == 0.0
    assert result.actual_load == 25.0
    assert result.status == "unplanned"


def test_comparison_without_prescription_and_without_activity_is_unplanned() -> None:
    service = create_service(
        sessions=[],
        actual=create_actual(
            duration_minutes=0,
            measured_load=0.0,
            activities_count=0,
        ),
    )

    result = service.calculate(
        uuid4(),
        TARGET_DATE,
    )

    assert result.planned_load == 0.0
    assert result.actual_load == 0.0
    assert result.status == "unplanned"
