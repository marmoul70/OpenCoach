from datetime import date
from uuid import UUID, uuid4

import pytest

from opencoach.coaching import (
    CoachDecisionService,
    CoachDecisionServiceError,
    PlannedSessionUnavailableError,
)
from opencoach.config import (
    load_threshold_settings,
)
from opencoach.database.repositories.training_session import (
    TrainingSessionRepository,
)
from opencoach.models import (
    Activity,
    TrainingSession,
)
from opencoach.readiness import (
    DailyReadiness,
    MetricBaseline,
    MetricComparison,
    ReadinessAssessment,
    ReadinessBaseline,
    ReadinessComparison,
)
from opencoach.models import WellnessDay


TARGET_DATE = date(
    2026,
    8,
    18,
)


class FakeTrainingSessionRepository(
    TrainingSessionRepository
):
    def __init__(
        self,
        sessions: list[TrainingSession],
    ) -> None:
        self.sessions = sessions
        self.list_calls = []

    def save_session(
        self,
        athlete_profile_id: UUID,
        session: TrainingSession,
    ) -> TrainingSession:
        raise NotImplementedError

    def get_session(
        self,
        athlete_profile_id: UUID,
        session_id: UUID,
    ) -> TrainingSession | None:
        raise NotImplementedError

    def list_sessions_between(
        self,
        athlete_profile_id: UUID,
        start_date: date,
        end_date: date,
    ) -> list[TrainingSession]:
        self.list_calls.append(
            (
                athlete_profile_id,
                start_date,
                end_date,
            )
        )

        return [
            session
            for session in self.sessions
            if (
                start_date
                <= session.date
                <= end_date
            )
        ]

    def update_status(
        self,
        athlete_profile_id: UUID,
        session_id: UUID,
        status: str,
    ) -> TrainingSession:
        raise NotImplementedError

    def link_activity(
        self,
        athlete_profile_id: UUID,
        session_id: UUID,
        activity_id: UUID | None,
    ) -> TrainingSession:
        raise NotImplementedError

    def list_candidate_activities_for_date(
        self,
        athlete_profile_id: UUID,
        session_date: date,
    ) -> list[Activity]:
        raise NotImplementedError


class FakeReadinessService:
    def __init__(
        self,
        assessment: ReadinessAssessment,
    ) -> None:
        self.assessment = assessment
        self.calls = []

    def calculate(
        self,
        athlete_profile_id: UUID,
        target_date: date,
    ) -> ReadinessAssessment:
        self.calls.append(
            (
                athlete_profile_id,
                target_date,
            )
        )

        return self.assessment


def create_session(
    *,
    status: str = "planned",
    duration_minutes: int = 60,
    intensity: str = "high",
) -> TrainingSession:
    return TrainingSession(
        id=uuid4(),
        date=TARGET_DATE,
        type="intervals",
        sport_type="Run",
        title="Fractionné",
        description="Séance qualitative.",
        duration_minutes=duration_minutes,
        distance_km=10.0,
        elevation_gain_m=100.0,
        intensity=intensity,
        heart_rate_zone="Z4",
        status=status,
    )


def create_readiness_assessment(
    *,
    score: float,
    constraints: tuple[str, ...] = (),
) -> ReadinessAssessment:
    current = WellnessDay(
        provider="intervals",
        date=TARGET_DATE,
        fitness_ctl=40.0,
        fatigue_atl=35.0,
        hrv=50.0,
        resting_hr=47,
        sleep_seconds=25200,
        sleep_score=78.0,
    )

    baseline = ReadinessBaseline(
        start_date=date(
            2026,
            8,
            4,
        ),
        end_date=date(
            2026,
            8,
            17,
        ),
        hrv=MetricBaseline(
            median=52.0,
            sample_count=14,
            reliable=True,
        ),
        resting_hr=MetricBaseline(
            median=46.0,
            sample_count=14,
            reliable=True,
        ),
        sleep_seconds=MetricBaseline(
            median=27000.0,
            sample_count=14,
            reliable=True,
        ),
        sleep_score=MetricBaseline(
            median=80.0,
            sample_count=14,
            reliable=True,
        ),
    )

    comparison = ReadinessComparison(
        hrv=MetricComparison(
            current=50.0,
            baseline=52.0,
            absolute_delta=-2.0,
            percent_delta=-3.8,
            reliable=True,
        ),
        resting_hr=MetricComparison(
            current=47.0,
            baseline=46.0,
            absolute_delta=1.0,
            percent_delta=2.2,
            reliable=True,
        ),
        sleep_seconds=MetricComparison(
            current=25200.0,
            baseline=27000.0,
            absolute_delta=-1800.0,
            percent_delta=-6.7,
            reliable=True,
        ),
        sleep_score=MetricComparison(
            current=78.0,
            baseline=80.0,
            absolute_delta=-2.0,
            percent_delta=-2.5,
            reliable=True,
        ),
    )

    readiness = DailyReadiness(
        score=score,
        level="moderate",
        signals=(),
        warning_count=0,
        critical_count=0,
        training_constraints=constraints,
        fitness_ctl=40.0,
        fatigue_atl=35.0,
        training_balance=5.0,
    )

    return ReadinessAssessment(
        date=TARGET_DATE,
        provider="intervals",
        current=current,
        baseline=baseline,
        comparison=comparison,
        context=None,
        readiness=readiness,
    )


def create_service(
    *,
    sessions: list[TrainingSession],
    readiness_score: float,
    constraints: tuple[str, ...] = (),
):
    training_repository = (
        FakeTrainingSessionRepository(
            sessions
        )
    )

    readiness_service = FakeReadinessService(
        create_readiness_assessment(
            score=readiness_score,
            constraints=constraints,
        )
    )

    service = CoachDecisionService(
        training_repository,
        readiness_service,
        thresholds=load_threshold_settings(),
    )

    return (
        service,
        training_repository,
        readiness_service,
    )


def test_coach_decision_service_keeps_session() -> None:
    session = create_session()

    service, repository, readiness_service = (
        create_service(
            sessions=[
                session,
            ],
            readiness_score=90.0,
        )
    )

    profile_id = uuid4()

    result = service.calculate(
        profile_id,
        TARGET_DATE,
    )

    assert result.date == TARGET_DATE
    assert result.session == session

    assert result.decision.action == "keep"

    assert (
        result.decision.recommended_duration_minutes
        == 60
    )

    assert repository.list_calls == [
        (
            profile_id,
            TARGET_DATE,
            TARGET_DATE,
        )
    ]

    assert readiness_service.calls == [
        (
            profile_id,
            TARGET_DATE,
        )
    ]


def test_coach_decision_service_reduces_session() -> None:
    service, _, _ = create_service(
        sessions=[
            create_session(),
        ],
        readiness_score=50.0,
        constraints=(
            "avoid_high_intensity",
        ),
    )

    result = service.calculate(
        uuid4(),
        TARGET_DATE,
    )

    assert result.decision.action == "reduce"

    assert (
        result.decision.recommended_intensity
        == "easy"
    )

    assert (
        result.decision.recommended_duration_minutes
        == 36
    )


def test_coach_decision_service_replaces_session() -> None:
    service, _, _ = create_service(
        sessions=[
            create_session(
                duration_minutes=75,
            ),
        ],
        readiness_score=40.0,
    )

    result = service.calculate(
        uuid4(),
        TARGET_DATE,
    )

    assert result.decision.action == "replace"

    assert (
        result.decision.recommended_duration_minutes
        == 45
    )

    assert (
        result.decision.recommended_intensity
        == "recovery"
    )


def test_coach_decision_service_rests() -> None:
    service, _, _ = create_service(
        sessions=[
            create_session(),
        ],
        readiness_score=20.0,
    )

    result = service.calculate(
        uuid4(),
        TARGET_DATE,
    )

    assert result.decision.action == "rest"

    assert (
        result.decision.recommended_duration_minutes
        is None
    )


def test_coach_decision_service_ignores_non_planned_session() -> None:
    service, _, readiness_service = create_service(
        sessions=[
            create_session(
                status="completed",
            ),
        ],
        readiness_score=90.0,
    )

    with pytest.raises(
        PlannedSessionUnavailableError,
    ):
        service.calculate(
            uuid4(),
            TARGET_DATE,
        )

    assert readiness_service.calls == []


def test_coach_decision_service_raises_when_no_session() -> None:
    service, _, readiness_service = create_service(
        sessions=[],
        readiness_score=90.0,
    )

    with pytest.raises(
        PlannedSessionUnavailableError,
    ):
        service.calculate(
            uuid4(),
            TARGET_DATE,
        )

    assert readiness_service.calls == []


def test_coach_decision_service_raises_when_multiple_sessions() -> None:
    service, _, readiness_service = create_service(
        sessions=[
            create_session(),
            create_session(),
        ],
        readiness_score=90.0,
    )

    with pytest.raises(
        CoachDecisionServiceError,
        match="Plusieurs séances planifiées",
    ):
        service.calculate(
            uuid4(),
            TARGET_DATE,
        )

    assert readiness_service.calls == []


def test_completed_session_does_not_conflict_with_planned_session() -> None:
    planned = create_session()

    service, _, _ = create_service(
        sessions=[
            create_session(
                status="completed",
            ),
            planned,
        ],
        readiness_score=90.0,
    )

    result = service.calculate(
        uuid4(),
        TARGET_DATE,
    )

    assert result.session == planned
    assert result.decision.action == "keep"
