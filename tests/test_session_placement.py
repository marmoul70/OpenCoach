from datetime import date
from uuid import uuid4

from opencoach.models import (
    AthleteProfile,
    TrainingSession,
)
from opencoach.planning import (
    build_session_placement_context,
    build_weekly_availability,
)


WEEK_START = date(
    2026,
    8,
    24,
)


def create_athlete() -> AthleteProfile:
    athlete = AthleteProfile()

    athlete.training.available_days = [
        0,
        2,
        4,
        6,
    ]

    return athlete


def create_session(
    *,
    session_date: date,
    intensity: str = "easy",
    session_type: str = "run",
) -> TrainingSession:
    return TrainingSession(
        id=uuid4(),
        date=session_date,
        type=session_type,
        sport_type="run",
        title="Séance test",
        description="",
        duration_minutes=60,
        intensity=intensity,
    )


def test_builds_context_with_previous_and_next_session() -> None:
    athlete = create_athlete()

    week = build_weekly_availability(
        athlete=athlete,
        week_start=WEEK_START,
    )

    target = create_session(
        session_date=date(
            2026,
            8,
            26,
        ),
        intensity="hard",
    )

    previous = create_session(
        session_date=date(
            2026,
            8,
            25,
        ),
    )

    next_session = create_session(
        session_date=date(
            2026,
            8,
            28,
        ),
    )

    context = build_session_placement_context(
        session=target,
        week=week,
        existing_sessions=(
            previous,
            target,
            next_session,
        ),
    )

    assert context.session is target

    assert context.original_date == date(
        2026,
        8,
        26,
    )

    assert context.previous_session is previous
    assert context.next_session is next_session


def test_target_session_is_removed_from_existing_sessions() -> None:
    athlete = create_athlete()

    week = build_weekly_availability(
        athlete=athlete,
        week_start=WEEK_START,
    )

    target = create_session(
        session_date=date(
            2026,
            8,
            26,
        )
    )

    context = build_session_placement_context(
        session=target,
        week=week,
        existing_sessions=(
            target,
        ),
    )

    assert context.existing_sessions == ()


def test_detects_hard_session_previous_day() -> None:
    athlete = create_athlete()

    week = build_weekly_availability(
        athlete=athlete,
        week_start=WEEK_START,
    )

    target = create_session(
        session_date=date(
            2026,
            8,
            26,
        )
    )

    previous = create_session(
        session_date=date(
            2026,
            8,
            25,
        ),
        intensity="hard",
    )

    context = build_session_placement_context(
        session=target,
        week=week,
        existing_sessions=(
            target,
            previous,
        ),
    )

    assert context.previous_day_hard is True


def test_detects_hard_session_next_day() -> None:
    athlete = create_athlete()

    week = build_weekly_availability(
        athlete=athlete,
        week_start=WEEK_START,
    )

    target = create_session(
        session_date=date(
            2026,
            8,
            26,
        )
    )

    next_session = create_session(
        session_date=date(
            2026,
            8,
            27,
        ),
        intensity="very_hard",
    )

    context = build_session_placement_context(
        session=target,
        week=week,
        existing_sessions=(
            target,
            next_session,
        ),
    )

    assert context.next_day_hard is True


def test_easy_adjacent_sessions_are_not_hard() -> None:
    athlete = create_athlete()

    week = build_weekly_availability(
        athlete=athlete,
        week_start=WEEK_START,
    )

    target = create_session(
        session_date=date(
            2026,
            8,
            26,
        )
    )

    previous = create_session(
        session_date=date(
            2026,
            8,
            25,
        ),
        intensity="easy",
    )

    next_session = create_session(
        session_date=date(
            2026,
            8,
            27,
        ),
        intensity="moderate",
    )

    context = build_session_placement_context(
        session=target,
        week=week,
        existing_sessions=(
            previous,
            target,
            next_session,
        ),
    )

    assert context.previous_day_hard is False
    assert context.next_day_hard is False


def test_rest_session_is_not_hard_even_with_high_intensity() -> None:
    athlete = create_athlete()

    week = build_weekly_availability(
        athlete=athlete,
        week_start=WEEK_START,
    )

    target = create_session(
        session_date=date(
            2026,
            8,
            26,
        )
    )

    rest = create_session(
        session_date=date(
            2026,
            8,
            25,
        ),
        intensity="very_hard",
        session_type="rest",
    )

    context = build_session_placement_context(
        session=target,
        week=week,
        existing_sessions=(
            rest,
            target,
        ),
    )

    assert context.previous_day_hard is False
