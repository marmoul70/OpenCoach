from datetime import date
from uuid import uuid4

from opencoach.coaching.daily_session_replanning import (
    DailyReplanningAction,
)
from opencoach.coaching.daily_session_replanning_service import (
    DailySessionReplanningService,
)
from opencoach.models import (
    AthleteConstraint,
    AthleteProfile,
    TrainingSession,
)


WEEK_START = date(
    2026,
    8,
    24,
)

THURSDAY = date(
    2026,
    8,
    27,
)

FRIDAY = date(
    2026,
    8,
    28,
)

SATURDAY = date(
    2026,
    8,
    29,
)

SUNDAY = date(
    2026,
    8,
    30,
)


def _athlete() -> AthleteProfile:
    athlete = AthleteProfile()

    athlete.training.available_days = [
        0,
        2,
        4,
        6,
    ]

    return athlete


def _session(
    *,
    session_date: date,
    session_type: str,
    intensity: str,
    status: str = "planned",
    duration_minutes: int = 60,
) -> TrainingSession:
    return TrainingSession(
        id=uuid4(),
        date=session_date,
        type=session_type,
        sport_type="Run",
        title=session_type,
        description="",
        duration_minutes=duration_minutes,
        intensity=intensity,
        status=status,
    )


class FakeTrainingSessionRepository:
    def __init__(
        self,
        sessions,
    ) -> None:
        self.sessions = list(
            sessions
        )

    def list_sessions_between(
        self,
        athlete_profile_id,
        start_date,
        end_date,
    ):
        del athlete_profile_id

        return [
            session
            for session in self.sessions
            if (
                start_date
                <= session.date
                <= end_date
            )
        ]


class FakeAthleteConstraintRepository:
    def __init__(
        self,
        constraints=(),
    ) -> None:
        self.constraints = list(
            constraints
        )

    def list_overlapping(
        self,
        athlete_profile_id,
        start_date,
        end_date,
    ):
        del athlete_profile_id

        return [
            constraint
            for constraint in self.constraints
            if (
                constraint.start_date
                <= end_date
                and constraint.end_date
                >= start_date
            )
        ]


def _build_service(
    *,
    sessions,
    constraints=(),
):
    return DailySessionReplanningService(
        training_session_repository=(
            FakeTrainingSessionRepository(
                sessions
            )
        ),
        athlete_constraint_repository=(
            FakeAthleteConstraintRepository(
                constraints
            )
        ),
    )


def test_service_proposes_saturday_even_when_not_preferred() -> None:
    athlete = _athlete()

    source = _session(
        session_date=THURSDAY,
        session_type="threshold",
        intensity="hard",
        status="skipped",
    )

    friday_easy = _session(
        session_date=FRIDAY,
        session_type="aerobic_easy",
        intensity="easy",
        duration_minutes=45,
    )

    sunday_trail = _session(
        session_date=SUNDAY,
        session_type="long_endurance",
        intensity="hard",
        duration_minutes=120,
    )

    service = _build_service(
        sessions=(
            source,
            friday_easy,
            sunday_trail,
        ),
    )

    proposal = service.propose(
        athlete_profile_id=uuid4(),
        athlete=athlete,
        session=source,
    )

    assert proposal is not None

    unchanged = next(
        option
        for option in proposal.options
        if (
            option.action
            is DailyReplanningAction
            .MOVE_UNCHANGED
        )
    )

    adapted = next(
        option
        for option in proposal.options
        if (
            option.action
            is DailyReplanningAction
            .MOVE_ADAPTED
        )
    )

    assert unchanged.target_date == SATURDAY
    assert adapted.target_date == SATURDAY
    assert adapted.recommended is True


def test_unavailable_saturday_is_never_proposed() -> None:
    athlete = _athlete()

    source = _session(
        session_date=THURSDAY,
        session_type="threshold",
        intensity="hard",
        status="skipped",
    )

    friday_easy = _session(
        session_date=FRIDAY,
        session_type="aerobic_easy",
        intensity="easy",
    )

    sunday_trail = _session(
        session_date=SUNDAY,
        session_type="long_endurance",
        intensity="hard",
        duration_minutes=120,
    )

    saturday_unavailable = (
        AthleteConstraint(
            id=uuid4(),
            start_date=SATURDAY,
            end_date=SATURDAY,
            constraint_type="personal",
            availability="unavailable",
            running_allowed=False,
            cross_training_allowed=False,
        )
    )

    service = _build_service(
        sessions=(
            source,
            friday_easy,
            sunday_trail,
        ),
        constraints=(
            saturday_unavailable,
        ),
    )

    proposal = service.propose(
        athlete_profile_id=uuid4(),
        athlete=athlete,
        session=source,
    )

    assert proposal is not None

    assert all(
        option.target_date != SATURDAY
        for option in proposal.options
    )


def test_non_skipped_session_returns_no_proposal() -> None:
    athlete = _athlete()

    source = _session(
        session_date=THURSDAY,
        session_type="threshold",
        intensity="hard",
        status="planned",
    )

    service = _build_service(
        sessions=(
            source,
        ),
    )

    proposal = service.propose(
        athlete_profile_id=uuid4(),
        athlete=athlete,
        session=source,
    )

    assert proposal is None
