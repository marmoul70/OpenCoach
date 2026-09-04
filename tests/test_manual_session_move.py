from datetime import (
    date,
    timedelta,
)
from uuid import uuid4

import pytest

from opencoach.coaching.manual_session_move import (
    ManualSessionMoveError,
    classify_session_load,
    evaluate_manual_session_move,
)
from opencoach.models import (
    TrainingSession,
)
from opencoach.planning.athlete.availability import (
    DayAvailability,
)
from opencoach.planning.athlete.weekly_availability import (
    WeeklyAvailability,
)


MONDAY = date(
    2026,
    9,
    7,
)


def make_session(
    *,
    day: int,
    session_type: str,
    intensity: str = "moderate",
    sport_type: str = "run",
    title: str = "Séance",
    duration: int = 60,
    status: str = "planned",
    activity=False,
):
    return TrainingSession(
        id=uuid4(),
        date=(
            MONDAY
            + timedelta(
                days=day
            )
        ),
        type=session_type,
        sport_type=sport_type,
        title=title,
        description="",
        duration_minutes=duration,
        intensity=intensity,
        status=status,
        activity_id=(
            uuid4()
            if activity
            else None
        ),
    )


def make_week(
    *,
    unavailable: set[int] | None = None,
    limited: dict[int, int] | None = None,
    preferred: set[int] | None = None,
):
    unavailable = (
        unavailable
        or set()
    )

    limited = (
        limited
        or {}
    )

    preferred = (
        preferred
        if preferred is not None
        else set(
            range(7)
        )
    )

    days = []

    for offset in range(7):
        target = (
            MONDAY
            + timedelta(
                days=offset
            )
        )

        if offset in unavailable:
            days.append(
                DayAvailability(
                    date=target,
                    preferred=(
                        offset
                        in preferred
                    ),
                    status="unavailable",
                    training_allowed=False,
                    requires_confirmation=False,
                    running_allowed=False,
                    cross_training_allowed=False,
                    max_duration_minutes=None,
                    constraints=(),
                )
            )

            continue

        if offset in limited:
            days.append(
                DayAvailability(
                    date=target,
                    preferred=(
                        offset
                        in preferred
                    ),
                    status="limited",
                    training_allowed=True,
                    requires_confirmation=False,
                    running_allowed=True,
                    cross_training_allowed=True,
                    max_duration_minutes=(
                        limited[offset]
                    ),
                    constraints=(),
                )
            )

            continue

        is_preferred = (
            offset
            in preferred
        )

        days.append(
            DayAvailability(
                date=target,
                preferred=is_preferred,
                status=(
                    "preferred"
                    if is_preferred
                    else "non_preferred"
                ),
                training_allowed=True,
                requires_confirmation=(
                    not is_preferred
                ),
                running_allowed=True,
                cross_training_allowed=True,
                max_duration_minutes=None,
                constraints=(),
            )
        )

    return WeeklyAvailability(
        start_date=MONDAY,
        end_date=(
            MONDAY
            + timedelta(
                days=6
            )
        ),
        days=tuple(days),
    )


def evaluation_for(
    plan,
    offset: int,
):
    target = (
        MONDAY
        + timedelta(
            days=offset
        )
    )

    return next(
        item
        for item in plan.days
        if item.date == target
    )


def test_classifies_training_load():
    assert (
        classify_session_load(
            make_session(
                day=1,
                session_type="strength_lower_body",
                sport_type="strength",
            )
        )
        == "strength"
    )

    assert (
        classify_session_load(
            make_session(
                day=1,
                session_type="threshold",
                intensity="hard",
            )
        )
        == "quality"
    )

    assert (
        classify_session_load(
            make_session(
                day=1,
                session_type="long_endurance",
            )
        )
        == "long"
    )

    assert (
        classify_session_load(
            make_session(
                day=1,
                session_type="aerobic_easy",
                intensity="easy",
            )
        )
        == "easy"
    )



def test_explicit_easy_type_wins_over_stale_strength_sport_type():
    session = make_session(
        day=1,
        session_type="aerobic_easy",
        intensity="easy",
        sport_type="strength",
    )

    assert (
        classify_session_load(
            session
        )
        == "easy"
    )


def test_explicit_quality_type_wins_over_stale_strength_sport_type():
    session = make_session(
        day=1,
        session_type="threshold",
        intensity="hard",
        sport_type="strength",
    )

    assert (
        classify_session_load(
            session
        )
        == "quality"
    )


def test_plan_contains_seven_days():
    session = make_session(
        day=1,
        session_type="strength_lower_body",
        sport_type="strength",
    )

    plan = evaluate_manual_session_move(
        session=session,
        week=make_week(),
        existing_sessions=(
            session,
        ),
        reference_date=MONDAY,
    )

    assert len(
        plan.days
    ) == 7

    current = evaluation_for(
        plan,
        1,
    )

    assert current.current is True
    assert current.selectable is False
    assert current.level == "current"


def test_past_days_are_impossible():
    session = make_session(
        day=2,
        session_type="strength_lower_body",
        sport_type="strength",
    )

    plan = evaluate_manual_session_move(
        session=session,
        week=make_week(),
        existing_sessions=(
            session,
        ),
        reference_date=(
            MONDAY
            + timedelta(
                days=2
            )
        ),
    )

    monday = evaluation_for(
        plan,
        0,
    )

    assert monday.score == 0
    assert monday.selectable is False
    assert monday.level == "impossible"

    assert (
        "Cette journée est déjà passée."
        in monday.blocking_reasons
    )


def test_strength_same_day_as_long_is_impossible():
    strength = make_session(
        day=1,
        session_type="strength_lower_body",
        sport_type="strength",
    )

    long_run = make_session(
        day=5,
        session_type="long_endurance",
        intensity="moderate",
        title="Sortie longue",
    )

    plan = evaluate_manual_session_move(
        session=strength,
        week=make_week(),
        existing_sessions=(
            strength,
            long_run,
        ),
        reference_date=MONDAY,
    )

    saturday = evaluation_for(
        plan,
        5,
    )

    assert saturday.score == 0
    assert saturday.selectable is False

    assert any(
        "grosse séance"
        in reason
        for reason
        in saturday.blocking_reasons
    )


def test_quality_same_day_as_long_is_impossible():
    hills = make_session(
        day=1,
        session_type="interval",
        intensity="hard",
        title="Côtes",
    )

    long_run = make_session(
        day=5,
        session_type="long_endurance",
        title="Sortie longue",
    )

    plan = evaluate_manual_session_move(
        session=hills,
        week=make_week(),
        existing_sessions=(
            hills,
            long_run,
        ),
        reference_date=MONDAY,
    )

    saturday = evaluation_for(
        plan,
        5,
    )

    assert saturday.selectable is False
    assert saturday.level == "impossible"


def test_strength_next_to_quality_is_discouraged_not_blocked():
    strength = make_session(
        day=1,
        session_type="strength_lower_body",
        sport_type="strength",
    )

    interval = make_session(
        day=4,
        session_type="interval",
        intensity="hard",
        title="Fractionné",
    )

    plan = evaluate_manual_session_move(
        session=strength,
        week=make_week(),
        existing_sessions=(
            strength,
            interval,
        ),
        reference_date=MONDAY,
    )

    thursday = evaluation_for(
        plan,
        3,
    )

    assert thursday.selectable is True

    assert any(
        "le lendemain"
        in reason
        and "compromettre"
        in reason
        for reason
        in thursday.reasons
    )


def test_empty_day_scores_higher_than_strength_before_interval():
    strength = make_session(
        day=1,
        session_type="strength_lower_body",
        sport_type="strength",
    )

    interval = make_session(
        day=4,
        session_type="interval",
        intensity="hard",
        title="Fractionné",
    )

    plan = evaluate_manual_session_move(
        session=strength,
        week=make_week(),
        existing_sessions=(
            strength,
            interval,
        ),
        reference_date=(
            MONDAY
            + timedelta(
                days=1
            )
        ),
    )

    thursday = evaluation_for(
        plan,
        3,
    )

    saturday = evaluation_for(
        plan,
        5,
    )

    assert saturday.score > thursday.score

    assert plan.best_date in {
        (
            MONDAY
            + timedelta(
                days=2
            )
        ),
        (
            MONDAY
            + timedelta(
                days=5
            )
        ),
        (
            MONDAY
            + timedelta(
                days=6
            )
        ),
    }


def test_strength_and_easy_same_day_remains_possible():
    strength = make_session(
        day=1,
        session_type="strength_lower_body",
        sport_type="strength",
    )

    easy = make_session(
        day=3,
        session_type="aerobic_easy",
        intensity="easy",
        title="Footing facile",
    )

    plan = evaluate_manual_session_move(
        session=strength,
        week=make_week(),
        existing_sessions=(
            strength,
            easy,
        ),
        reference_date=MONDAY,
    )

    thursday = evaluation_for(
        plan,
        3,
    )

    assert thursday.selectable is True
    assert thursday.score > 0

    assert any(
        "cumul reste possible"
        in reason
        for reason
        in thursday.reasons
    )


def test_unavailable_day_is_impossible():
    session = make_session(
        day=1,
        session_type="aerobic_easy",
        intensity="easy",
    )

    plan = evaluate_manual_session_move(
        session=session,
        week=make_week(
            unavailable={
                3,
            }
        ),
        existing_sessions=(
            session,
        ),
        reference_date=MONDAY,
    )

    thursday = evaluation_for(
        plan,
        3,
    )

    assert thursday.score == 0
    assert thursday.selectable is False


def test_duration_limit_is_enforced():
    session = make_session(
        day=1,
        session_type="aerobic_easy",
        intensity="easy",
        duration=90,
    )

    plan = evaluate_manual_session_move(
        session=session,
        week=make_week(
            limited={
                3: 45,
            }
        ),
        existing_sessions=(
            session,
        ),
        reference_date=MONDAY,
    )

    thursday = evaluation_for(
        plan,
        3,
    )

    assert thursday.selectable is False

    assert any(
        "durée"
        in reason.lower()
        for reason
        in thursday.blocking_reasons
    )


def test_completed_session_cannot_be_moved():
    session = make_session(
        day=1,
        session_type="aerobic_easy",
        intensity="easy",
        status="completed",
    )

    with pytest.raises(
        ManualSessionMoveError,
        match="planifiée",
    ):
        evaluate_manual_session_move(
            session=session,
            week=make_week(),
            existing_sessions=(
                session,
            ),
            reference_date=MONDAY,
        )


def test_session_with_activity_cannot_be_moved():
    session = make_session(
        day=1,
        session_type="aerobic_easy",
        intensity="easy",
        activity=True,
    )

    with pytest.raises(
        ManualSessionMoveError,
        match="activité",
    ):
        evaluate_manual_session_move(
            session=session,
            week=make_week(),
            existing_sessions=(
                session,
            ),
            reference_date=MONDAY,
        )


def test_move_only_during_current_week():
    session = make_session(
        day=1,
        session_type="aerobic_easy",
        intensity="easy",
    )

    with pytest.raises(
        ManualSessionMoveError,
        match="semaine en cours",
    ):
        evaluate_manual_session_move(
            session=session,
            week=make_week(),
            existing_sessions=(
                session,
            ),
            reference_date=(
                MONDAY
                + timedelta(
                    days=8
                )
            ),
        )


def test_best_day_is_marked_recommended():
    session = make_session(
        day=1,
        session_type="strength_lower_body",
        sport_type="strength",
    )

    interval = make_session(
        day=4,
        session_type="interval",
        intensity="hard",
    )

    plan = evaluate_manual_session_move(
        session=session,
        week=make_week(),
        existing_sessions=(
            session,
            interval,
        ),
        reference_date=(
            MONDAY
            + timedelta(
                days=1
            )
        ),
    )

    recommended = [
        item
        for item in plan.days
        if item.recommended
    ]

    assert len(
        recommended
    ) == 1

    assert (
        recommended[0].date
        == plan.best_date
    )

    assert recommended[0].selectable
