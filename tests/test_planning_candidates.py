from datetime import date
from uuid import uuid4

from opencoach.models import (
    AthleteConstraint,
    AthleteProfile,
)
from opencoach.planning import (
    build_weekly_availability,
    rank_training_day_candidates,
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


def create_constraint(
    *,
    target_date: date,
    availability: str,
    running_allowed: bool = True,
    cross_training_allowed: bool = True,
    max_duration_minutes: int | None = None,
) -> AthleteConstraint:
    return AthleteConstraint(
        id=uuid4(),
        start_date=target_date,
        end_date=target_date,
        constraint_type="personal",
        availability=availability,
        running_allowed=running_allowed,
        cross_training_allowed=cross_training_allowed,
        max_duration_minutes=max_duration_minutes,
    )


def test_unavailable_original_day_is_not_candidate() -> None:
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

    candidates = rank_training_day_candidates(
        week=week,
        original_date=WEDNESDAY,
    )

    dates = {
        candidate.date
        for candidate in candidates
    }

    assert WEDNESDAY not in dates


def test_thursday_ranks_before_tuesday_when_otherwise_equal() -> None:
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

    candidates = rank_training_day_candidates(
        week=week,
        original_date=WEDNESDAY,
    )

    assert candidates[0].date == date(
        2026,
        8,
        27,
    )

    assert candidates[1].date == date(
        2026,
        8,
        25,
    )


def test_preferred_day_receives_preference_bonus() -> None:
    athlete = create_athlete()

    week = build_weekly_availability(
        athlete=athlete,
        week_start=WEEK_START,
    )

    candidates = rank_training_day_candidates(
        week=week,
        original_date=WEDNESDAY,
    )

    friday = next(
        candidate
        for candidate in candidates
        if candidate.date
        == date(2026, 8, 28)
    )

    saturday = next(
        candidate
        for candidate in candidates
        if candidate.date
        == date(2026, 8, 29)
    )

    assert friday.preferred is True
    assert saturday.preferred is False

    assert friday.score > saturday.score


def test_non_preferred_candidate_requires_confirmation() -> None:
    athlete = create_athlete()

    week = build_weekly_availability(
        athlete=athlete,
        week_start=WEEK_START,
    )

    candidates = rank_training_day_candidates(
        week=week,
        original_date=WEDNESDAY,
    )

    thursday = next(
        candidate
        for candidate in candidates
        if candidate.date
        == date(2026, 8, 27)
    )

    assert thursday.preferred is False

    assert (
        thursday.requires_confirmation
        is True
    )


def test_confirmed_override_improves_candidate() -> None:
    athlete = create_athlete()

    thursday = date(
        2026,
        8,
        27,
    )

    override = create_constraint(
        target_date=thursday,
        availability="available_override",
    )

    week = build_weekly_availability(
        athlete=athlete,
        week_start=WEEK_START,
        constraints=(override,),
    )

    candidates = rank_training_day_candidates(
        week=week,
        original_date=WEDNESDAY,
    )

    candidate = next(
        item
        for item in candidates
        if item.date == thursday
    )

    assert (
        candidate.requires_confirmation
        is False
    )

    assert (
        "Disponibilité exceptionnelle confirmée."
        in candidate.reasons
    )


def test_running_candidate_excludes_running_forbidden_day() -> None:
    athlete = create_athlete()

    thursday = date(
        2026,
        8,
        27,
    )

    injury = create_constraint(
        target_date=thursday,
        availability="limited",
        running_allowed=False,
        cross_training_allowed=True,
    )

    week = build_weekly_availability(
        athlete=athlete,
        week_start=WEEK_START,
        constraints=(injury,),
    )

    candidates = rank_training_day_candidates(
        week=week,
        original_date=WEDNESDAY,
        for_running=True,
    )

    dates = {
        candidate.date
        for candidate in candidates
    }

    assert thursday not in dates


def test_cross_training_can_use_running_forbidden_day() -> None:
    athlete = create_athlete()

    thursday = date(
        2026,
        8,
        27,
    )

    injury = create_constraint(
        target_date=thursday,
        availability="limited",
        running_allowed=False,
        cross_training_allowed=True,
    )

    week = build_weekly_availability(
        athlete=athlete,
        week_start=WEEK_START,
        constraints=(injury,),
    )

    candidates = rank_training_day_candidates(
        week=week,
        original_date=WEDNESDAY,
        for_running=False,
    )

    dates = {
        candidate.date
        for candidate in candidates
    }

    assert thursday in dates


def test_candidate_preserves_duration_limit() -> None:
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

    candidates = rank_training_day_candidates(
        week=week,
        original_date=WEDNESDAY,
    )

    candidate = next(
        item
        for item in candidates
        if item.date == thursday
    )

    assert (
        candidate.max_duration_minutes
        == 45
    )
