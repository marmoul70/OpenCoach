from datetime import date
from uuid import uuid4

from opencoach.models import (
    AthleteConstraint,
    AthleteProfile,
    TrainingSession,
)
from opencoach.planning import (
    build_session_placement_context,
    build_weekly_availability,
)
from opencoach.planning.candidates import (
    rank_training_day_candidates,
)
from opencoach.planning.placement_rules import (
    evaluate_placement_rules,
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
    duration_minutes: int = 60,
) -> TrainingSession:
    return TrainingSession(
        id=uuid4(),
        date=session_date,
        type="run",
        sport_type="run",
        title="Séance test",
        description="",
        duration_minutes=duration_minutes,
        intensity=intensity,
    )


def get_candidate(
    *,
    context,
    target_date: date,
):
    candidates = rank_training_day_candidates(
        week=context.week,
        original_date=context.original_date,
        for_running=True,
    )

    return next(
        candidate
        for candidate in candidates
        if candidate.date == target_date
    )


def test_same_day_session_is_soft_rule() -> None:
    athlete = create_athlete()

    week = build_weekly_availability(
        athlete=athlete,
        week_start=WEEK_START,
    )

    target = create_session(
        session_date=WEDNESDAY,
    )

    thursday_session = create_session(
        session_date=date(
            2026,
            8,
            27,
        ),
    )

    context = build_session_placement_context(
        session=target,
        week=week,
        existing_sessions=(
            target,
            thursday_session,
        ),
    )

    candidate = get_candidate(
        context=context,
        target_date=date(
            2026,
            8,
            27,
        ),
    )

    results = evaluate_placement_rules(
        context=context,
        candidate=candidate,
    )

    result = next(
        item
        for item in results
        if item.rule_id
        == "existing_session_same_day"
    )

    assert result.violated is True
    assert result.severity == "soft"
    assert result.score_adjustment == -35


def test_hard_session_previous_day_is_hard_rule() -> None:
    athlete = create_athlete()

    week = build_weekly_availability(
        athlete=athlete,
        week_start=WEEK_START,
    )

    target = create_session(
        session_date=WEDNESDAY,
        intensity="hard",
    )

    wednesday_hard = create_session(
        session_date=WEDNESDAY,
        intensity="hard",
    )

    context = build_session_placement_context(
        session=target,
        week=week,
        existing_sessions=(
            target,
            wednesday_hard,
        ),
    )

    candidate = get_candidate(
        context=context,
        target_date=date(
            2026,
            8,
            27,
        ),
    )

    results = evaluate_placement_rules(
        context=context,
        candidate=candidate,
    )

    result = next(
        item
        for item in results
        if item.rule_id
        == "hard_session_previous_day"
    )

    assert result.violated is True
    assert result.severity == "hard"


def test_hard_session_next_day_is_hard_rule() -> None:
    athlete = create_athlete()

    week = build_weekly_availability(
        athlete=athlete,
        week_start=WEEK_START,
    )

    target = create_session(
        session_date=WEDNESDAY,
        intensity="hard",
    )

    friday_hard = create_session(
        session_date=date(
            2026,
            8,
            28,
        ),
        intensity="hard",
    )

    context = build_session_placement_context(
        session=target,
        week=week,
        existing_sessions=(
            target,
            friday_hard,
        ),
    )

    candidate = get_candidate(
        context=context,
        target_date=date(
            2026,
            8,
            27,
        ),
    )

    results = evaluate_placement_rules(
        context=context,
        candidate=candidate,
    )

    result = next(
        item
        for item in results
        if item.rule_id
        == "hard_session_next_day"
    )

    assert result.violated is True
    assert result.severity == "hard"


def test_duration_limit_is_hard_rule() -> None:
    athlete = create_athlete()

    thursday = date(
        2026,
        8,
        27,
    )

    constraint = AthleteConstraint(
        id=uuid4(),
        start_date=thursday,
        end_date=thursday,
        constraint_type="personal",
        availability="limited",
        running_allowed=True,
        cross_training_allowed=True,
        max_duration_minutes=45,
    )

    week = build_weekly_availability(
        athlete=athlete,
        week_start=WEEK_START,
        constraints=(constraint,),
    )

    target = create_session(
        session_date=WEDNESDAY,
        duration_minutes=60,
    )

    context = build_session_placement_context(
        session=target,
        week=week,
        existing_sessions=(
            target,
        ),
    )

    candidate = get_candidate(
        context=context,
        target_date=thursday,
    )

    results = evaluate_placement_rules(
        context=context,
        candidate=candidate,
    )

    result = next(
        item
        for item in results
        if item.rule_id
        == "duration_limit"
    )

    assert result.violated is True
    assert result.severity == "hard"


def test_non_violated_rules_have_no_adjustment() -> None:
    athlete = create_athlete()

    week = build_weekly_availability(
        athlete=athlete,
        week_start=WEEK_START,
    )

    target = create_session(
        session_date=WEDNESDAY,
        intensity="easy",
        duration_minutes=45,
    )

    context = build_session_placement_context(
        session=target,
        week=week,
        existing_sessions=(
            target,
        ),
    )

    candidate = get_candidate(
        context=context,
        target_date=date(
            2026,
            8,
            27,
        ),
    )

    results = evaluate_placement_rules(
        context=context,
        candidate=candidate,
    )

    assert all(
        not result.violated
        for result in results
    )

    assert all(
        result.score_adjustment == 0
        for result in results
    )
