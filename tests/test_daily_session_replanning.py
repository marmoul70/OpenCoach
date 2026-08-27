from datetime import date
from uuid import uuid4

from opencoach.coaching.daily_session_replanning import (
    DailyReplanningAction,
    DailyReplanningRisk,
    propose_daily_session_replanning,
)
from opencoach.models import (
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


def _scenario():
    athlete = _athlete()

    week = build_weekly_availability(
        athlete=athlete,
        week_start=WEEK_START,
    )

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

    return (
        week,
        source,
        (
            source,
            friday_easy,
            sunday_trail,
        ),
    )


def test_replanning_returns_three_options() -> None:
    week, source, sessions = (
        _scenario()
    )

    proposal = (
        propose_daily_session_replanning(
            session=source,
            week=week,
            existing_sessions=sessions,
            reference_date=THURSDAY,
        )
    )

    assert proposal is not None

    actions = {
        option.action
        for option in proposal.options
    }

    assert actions == {
        DailyReplanningAction.CANCEL,
        DailyReplanningAction.MOVE_UNCHANGED,
        DailyReplanningAction.MOVE_ADAPTED,
    }


def test_free_non_preferred_saturday_is_used() -> None:
    week, source, sessions = (
        _scenario()
    )

    proposal = (
        propose_daily_session_replanning(
            session=source,
            week=week,
            existing_sessions=sessions,
            reference_date=THURSDAY,
        )
    )

    assert proposal is not None

    moved = next(
        option
        for option in proposal.options
        if (
            option.action
            is DailyReplanningAction
            .MOVE_UNCHANGED
        )
    )

    assert moved.target_date == SATURDAY


def test_unchanged_hard_session_before_trail_is_high_risk() -> None:
    week, source, sessions = (
        _scenario()
    )

    proposal = (
        propose_daily_session_replanning(
            session=source,
            week=week,
            existing_sessions=sessions,
            reference_date=THURSDAY,
        )
    )

    assert proposal is not None

    moved = next(
        option
        for option in proposal.options
        if (
            option.action
            is DailyReplanningAction
            .MOVE_UNCHANGED
        )
    )

    assert (
        moved.risk
        is DailyReplanningRisk.HIGH
    )

    assert moved.recommended is False


def test_adapted_saturday_is_recommended() -> None:
    week, source, sessions = (
        _scenario()
    )

    proposal = (
        propose_daily_session_replanning(
            session=source,
            week=week,
            existing_sessions=sessions,
            reference_date=THURSDAY,
        )
    )

    assert proposal is not None

    adapted = next(
        option
        for option in proposal.options
        if (
            option.action
            is DailyReplanningAction
            .MOVE_ADAPTED
        )
    )

    assert adapted.target_date == SATURDAY
    assert adapted.recommended is True

    assert adapted.session is not None

    assert (
        adapted.session.type
        == "aerobic_easy"
    )

    assert (
        adapted.session.intensity
        == "easy"
    )

    assert (
        adapted.session.duration_minutes
        <= 45
    )


def test_exactly_one_option_is_recommended() -> None:
    week, source, sessions = (
        _scenario()
    )

    proposal = (
        propose_daily_session_replanning(
            session=source,
            week=week,
            existing_sessions=sessions,
            reference_date=THURSDAY,
        )
    )

    assert proposal is not None

    recommended = tuple(
        option
        for option in proposal.options
        if option.recommended
    )

    assert len(recommended) == 1

    assert (
        proposal.recommended_option
        == recommended[0]
    )


def test_strength_session_never_becomes_running_session() -> None:
    athlete = _athlete()

    week = build_weekly_availability(
        athlete=athlete,
        week_start=WEEK_START,
    )

    source = TrainingSession(
        id=uuid4(),
        date=THURSDAY,
        type="strength_lower_body",
        sport_type="Strength",
        title="Renforcement membres inférieurs",
        description="",
        duration_minutes=30,
        intensity="hard",
        status="skipped",
    )

    proposal = (
        propose_daily_session_replanning(
            session=source,
            week=week,
            existing_sessions=(
                source,
            ),
            reference_date=THURSDAY,
        )
    )

    assert proposal is not None

    adapted = next(
        option
        for option in proposal.options
        if (
            option.action
            is DailyReplanningAction
            .MOVE_ADAPTED
        )
    )

    assert adapted.session is not None

    assert (
        adapted.session.type
        == "strength_lower_body"
    )

    assert (
        adapted.session.sport_type
        == "Strength"
    )

    assert (
        adapted.session.type
        != "aerobic_easy"
    )

    assert (
        adapted.session.duration_minutes
        < source.duration_minutes
    )
