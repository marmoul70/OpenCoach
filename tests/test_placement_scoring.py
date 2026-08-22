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
    rank_session_placement_candidates,
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


def create_constraint(
    *,
    target_date: date,
    availability: str,
    max_duration_minutes: int | None = None,
) -> AthleteConstraint:
    return AthleteConstraint(
        id=uuid4(),
        start_date=target_date,
        end_date=target_date,
        constraint_type="personal",
        availability=availability,
        running_allowed=True,
        cross_training_allowed=True,
        max_duration_minutes=max_duration_minutes,
    )


def test_hard_session_avoids_hard_session_next_day() -> None:
    athlete = create_athlete()

    unavailable = create_constraint(
        target_date=WEDNESDAY,
        availability="unavailable",
    )

    week = build_weekly_availability(
        athlete=athlete,
        week_start=WEEK_START,
        constraints=(unavailable,),
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

    candidates = rank_session_placement_candidates(
        context=context,
    )

    assert candidates[0].date == date(
        2026,
        8,
        25,
    )

    thursday = next(
        candidate
        for candidate in candidates
        if candidate.date
        == date(2026, 8, 27)
    )

    assert (
        "Séance intense déjà prévue le lendemain."
        in thursday.reasons
    )


def test_hard_session_avoids_hard_session_previous_day() -> None:
    athlete = create_athlete()

    week = build_weekly_availability(
        athlete=athlete,
        week_start=WEEK_START,
    )

    target = create_session(
        session_date=WEDNESDAY,
        intensity="hard",
    )

    monday_hard = create_session(
        session_date=date(
            2026,
            8,
            24,
        ),
        intensity="hard",
    )

    context = build_session_placement_context(
        session=target,
        week=week,
        existing_sessions=(
            monday_hard,
            target,
        ),
    )

    candidates = rank_session_placement_candidates(
        context=context,
    )

    tuesday = next(
        candidate
        for candidate in candidates
        if candidate.date
        == date(2026, 8, 25)
    )

    assert (
        "Séance intense déjà prévue la veille."
        in tuesday.reasons
    )


def test_easy_session_is_not_penalized_by_adjacent_hard_session() -> None:
    athlete = create_athlete()

    week = build_weekly_availability(
        athlete=athlete,
        week_start=WEEK_START,
    )

    target = create_session(
        session_date=WEDNESDAY,
        intensity="easy",
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

    candidates = rank_session_placement_candidates(
        context=context,
    )

    thursday = next(
        candidate
        for candidate in candidates
        if candidate.date
        == date(2026, 8, 27)
    )

    assert (
        "Séance intense déjà prévue le lendemain."
        not in thursday.reasons
    )

    assert (
        thursday.placement_score
        == thursday.calendar_score
    )


def test_existing_session_on_candidate_day_is_penalized() -> None:
    athlete = create_athlete()

    week = build_weekly_availability(
        athlete=athlete,
        week_start=WEEK_START,
    )

    target = create_session(
        session_date=WEDNESDAY,
        intensity="easy",
    )

    thursday_session = create_session(
        session_date=date(
            2026,
            8,
            27,
        ),
        intensity="easy",
    )

    context = build_session_placement_context(
        session=target,
        week=week,
        existing_sessions=(
            target,
            thursday_session,
        ),
    )

    candidates = rank_session_placement_candidates(
        context=context,
    )

    thursday = next(
        candidate
        for candidate in candidates
        if candidate.date
        == date(2026, 8, 27)
    )

    assert (
        thursday.placement_score
        == thursday.calendar_score - 35
    )


def test_duration_limit_penalizes_too_long_session() -> None:
    athlete = create_athlete()

    thursday = date(
        2026,
        8,
        27,
    )

    limited = create_constraint(
        target_date=thursday,
        availability="limited",
        max_duration_minutes=45,
    )

    week = build_weekly_availability(
        athlete=athlete,
        week_start=WEEK_START,
        constraints=(limited,),
    )

    target = create_session(
        session_date=WEDNESDAY,
        intensity="easy",
        duration_minutes=60,
    )

    context = build_session_placement_context(
        session=target,
        week=week,
        existing_sessions=(target,),
    )

    candidates = rank_session_placement_candidates(
        context=context,
    )

    candidate = next(
        item
        for item in candidates
        if item.date == thursday
    )

    assert candidate.eligible is False

    assert (
        "Durée prévue supérieure à la disponibilité du jour."
        in candidate.reasons
    )


def test_duration_limit_does_not_penalize_compatible_session() -> None:
    athlete = create_athlete()

    thursday = date(
        2026,
        8,
        27,
    )

    limited = create_constraint(
        target_date=thursday,
        availability="limited",
        max_duration_minutes=60,
    )

    week = build_weekly_availability(
        athlete=athlete,
        week_start=WEEK_START,
        constraints=(limited,),
    )

    target = create_session(
        session_date=WEDNESDAY,
        duration_minutes=45,
    )

    context = build_session_placement_context(
        session=target,
        week=week,
        existing_sessions=(target,),
    )

    candidates = rank_session_placement_candidates(
        context=context,
    )

    candidate = next(
        item
        for item in candidates
        if item.date == thursday
    )

    assert (
        "Durée prévue supérieure à la disponibilité du jour."
        not in candidate.reasons
    )
def test_soft_rule_keeps_candidate_eligible() -> None:
    athlete = create_athlete()

    week = build_weekly_availability(
        athlete=athlete,
        week_start=WEEK_START,
    )

    target = create_session(
        session_date=WEDNESDAY,
        intensity="easy",
    )

    thursday_session = create_session(
        session_date=date(
            2026,
            8,
            27,
        ),
        intensity="easy",
    )

    context = build_session_placement_context(
        session=target,
        week=week,
        existing_sessions=(
            target,
            thursday_session,
        ),
    )

    candidates = rank_session_placement_candidates(
        context=context,
    )

    thursday = next(
        candidate
        for candidate in candidates
        if candidate.date
        == date(2026, 8, 27)
    )

    assert thursday.eligible is True

    assert (
        thursday.placement_score
        == thursday.calendar_score - 35
    )