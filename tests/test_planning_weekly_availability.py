from datetime import date
from uuid import uuid4

from opencoach.models import (
    AthleteConstraint,
    AthleteProfile,
)
from opencoach.planning import (
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


def test_builds_seven_day_week() -> None:
    week = build_weekly_availability(
        athlete=create_athlete(),
        week_start=WEEK_START,
    )

    assert week.start_date == date(
        2026,
        8,
        24,
    )

    assert week.end_date == date(
        2026,
        8,
        30,
    )

    assert len(week.days) == 7

    assert week.days[0].date == date(
        2026,
        8,
        24,
    )

    assert week.days[-1].date == date(
        2026,
        8,
        30,
    )


def test_identifies_preferred_training_days() -> None:
    week = build_weekly_availability(
        athlete=create_athlete(),
        week_start=WEEK_START,
    )

    dates = tuple(
        day.date
        for day in week.preferred_training_days()
    )

    assert dates == (
        date(2026, 8, 24),
        date(2026, 8, 26),
        date(2026, 8, 28),
        date(2026, 8, 30),
    )


def test_identifies_alternative_training_days() -> None:
    week = build_weekly_availability(
        athlete=create_athlete(),
        week_start=WEEK_START,
    )

    dates = tuple(
        day.date
        for day in week.alternative_training_days()
    )

    assert dates == (
        date(2026, 8, 25),
        date(2026, 8, 27),
        date(2026, 8, 29),
    )

    assert all(
        day.requires_confirmation
        for day in week.alternative_training_days()
    )


def test_unavailable_preferred_day_is_removed_from_training_days() -> None:
    athlete = create_athlete()

    wednesday = date(
        2026,
        8,
        26,
    )

    constraint = create_constraint(
        target_date=wednesday,
        availability="unavailable",
    )

    week = build_weekly_availability(
        athlete=athlete,
        week_start=WEEK_START,
        constraints=(constraint,),
    )

    day = week.get_day(
        wednesday
    )

    assert day is not None
    assert day.preferred is True
    assert day.status == "unavailable"

    training_dates = {
        item.date
        for item in week.training_days()
    }

    assert wednesday not in training_dates


def test_available_override_makes_alternative_day_confirmed() -> None:
    athlete = create_athlete()

    thursday = date(
        2026,
        8,
        27,
    )

    constraint = create_constraint(
        target_date=thursday,
        availability="available_override",
    )

    week = build_weekly_availability(
        athlete=athlete,
        week_start=WEEK_START,
        constraints=(constraint,),
    )

    day = week.get_day(
        thursday
    )

    assert day is not None
    assert day.preferred is False

    assert day.status == (
        "available_override"
    )

    assert day.training_allowed is True

    assert (
        day.requires_confirmation
        is False
    )


def test_limited_day_keeps_restrictions() -> None:
    athlete = create_athlete()

    friday = date(
        2026,
        8,
        28,
    )

    constraint = create_constraint(
        target_date=friday,
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

    day = week.get_day(
        friday
    )

    assert day is not None
    assert day.status == "limited"

    assert (
        day.max_duration_minutes
        == 45
    )


def test_get_day_returns_none_outside_week() -> None:
    week = build_weekly_availability(
        athlete=create_athlete(),
        week_start=WEEK_START,
    )

    assert week.get_day(
        date(
            2026,
            8,
            31,
        )
    ) is None
