from datetime import date
from uuid import uuid4

from opencoach.coaching.daily_session_rescheduling import (
    propose_daily_session_rescheduling,
)
from opencoach.models import (
    AthleteConstraint,
    AthleteProfile,
    TrainingSession,
)
from opencoach.planning import (
    build_weekly_availability,
)


WEEK_START = date(
    2026,
    8,
    24,
)

WEDNESDAY = date(
    2026,
    8,
    26,
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
    session_date: date = WEDNESDAY,
    session_type: str = "threshold",
    intensity: str = "hard",
    status: str = "skipped",
) -> TrainingSession:
    return TrainingSession(
        id=uuid4(),
        date=session_date,
        type=session_type,
        sport_type="Run",
        title="Séance test",
        description="",
        duration_minutes=60,
        intensity=intensity,
        status=status,
    )


def test_skipped_key_session_only_uses_future_candidates() -> None:
    athlete = _athlete()

    week = build_weekly_availability(
        athlete=athlete,
        week_start=WEEK_START,
    )

    session = _session()

    proposal = (
        propose_daily_session_rescheduling(
            session=session,
            week=week,
            existing_sessions=(
                session,
            ),
            reference_date=WEDNESDAY,
        )
    )

    assert proposal is not None

    assert (
        proposal.suggested_date
        > WEDNESDAY
    )


def test_skipped_key_session_never_returns_past_candidate() -> None:
    athlete = _athlete()

    week = build_weekly_availability(
        athlete=athlete,
        week_start=WEEK_START,
    )

    session = _session()

    proposal = (
        propose_daily_session_rescheduling(
            session=session,
            week=week,
            existing_sessions=(
                session,
            ),
            reference_date=WEDNESDAY,
        )
    )

    assert proposal is not None

    assert (
        proposal.suggested_date
        not in {
            date(
                2026,
                8,
                24,
            ),
            date(
                2026,
                8,
                25,
            ),
            WEDNESDAY,
        }
    )


def test_easy_session_is_not_proposed_for_rescheduling() -> None:
    athlete = _athlete()

    week = build_weekly_availability(
        athlete=athlete,
        week_start=WEEK_START,
    )

    session = _session(
        session_type="aerobic_easy",
        intensity="easy",
    )

    proposal = (
        propose_daily_session_rescheduling(
            session=session,
            week=week,
            existing_sessions=(
                session,
            ),
            reference_date=WEDNESDAY,
        )
    )

    assert proposal is None


def test_long_endurance_can_be_rescheduled() -> None:
    athlete = _athlete()

    week = build_weekly_availability(
        athlete=athlete,
        week_start=WEEK_START,
    )

    session = _session(
        session_type="long_endurance",
        intensity="moderate",
    )

    proposal = (
        propose_daily_session_rescheduling(
            session=session,
            week=week,
            existing_sessions=(
                session,
            ),
            reference_date=WEDNESDAY,
        )
    )

    assert proposal is not None

    assert (
        proposal.suggested_date
        > WEDNESDAY
    )


def test_no_future_available_day_returns_no_proposal() -> None:
    athlete = _athlete()

    constraints = tuple(
        AthleteConstraint(
            id=uuid4(),
            start_date=target_date,
            end_date=target_date,
            constraint_type="personal",
            availability="unavailable",
            running_allowed=False,
            cross_training_allowed=False,
        )
        for target_date in (
            date(
                2026,
                8,
                27,
            ),
            date(
                2026,
                8,
                28,
            ),
            date(
                2026,
                8,
                29,
            ),
            date(
                2026,
                8,
                30,
            ),
        )
    )

    week = build_weekly_availability(
        athlete=athlete,
        week_start=WEEK_START,
        constraints=constraints,
    )

    session = _session()

    proposal = (
        propose_daily_session_rescheduling(
            session=session,
            week=week,
            existing_sessions=(
                session,
            ),
            reference_date=WEDNESDAY,
        )
    )

    assert proposal is None


def test_non_skipped_session_is_not_rescheduled() -> None:
    athlete = _athlete()

    week = build_weekly_availability(
        athlete=athlete,
        week_start=WEEK_START,
    )

    session = _session(
        status="planned",
    )

    proposal = (
        propose_daily_session_rescheduling(
            session=session,
            week=week,
            existing_sessions=(
                session,
            ),
            reference_date=WEDNESDAY,
        )
    )

    assert proposal is None
