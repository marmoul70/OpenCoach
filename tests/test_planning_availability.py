from datetime import date
from uuid import uuid4

from opencoach.models import (
    AthleteConstraint,
    AthleteProfile,
)
from opencoach.planning import (
    resolve_day_availability,
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


def test_preferred_day_is_available() -> None:
    athlete = create_athlete()

    monday = date(
        2026,
        8,
        24,
    )

    result = resolve_day_availability(
        athlete=athlete,
        target_date=monday,
    )

    assert result.preferred is True
    assert result.status == "preferred"

    assert result.training_allowed is True
    assert result.requires_confirmation is False


def test_non_preferred_day_can_be_proposed() -> None:
    athlete = create_athlete()

    thursday = date(
        2026,
        8,
        27,
    )

    result = resolve_day_availability(
        athlete=athlete,
        target_date=thursday,
    )

    assert result.preferred is False

    assert result.status == (
        "non_preferred"
    )

    assert result.training_allowed is True

    assert (
        result.requires_confirmation
        is True
    )


def test_unavailable_constraint_blocks_preferred_day() -> None:
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

    result = resolve_day_availability(
        athlete=athlete,
        target_date=wednesday,
        constraints=(constraint,),
    )

    assert result.preferred is True
    assert result.status == "unavailable"

    assert result.training_allowed is False
    assert result.running_allowed is False

    assert (
        result.cross_training_allowed
        is False
    )


def test_available_override_opens_non_preferred_day() -> None:
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

    result = resolve_day_availability(
        athlete=athlete,
        target_date=thursday,
        constraints=(constraint,),
    )

    assert result.preferred is False

    assert result.status == (
        "available_override"
    )

    assert result.training_allowed is True

    assert (
        result.requires_confirmation
        is False
    )


def test_injury_can_block_running_only() -> None:
    athlete = create_athlete()

    wednesday = date(
        2026,
        8,
        26,
    )

    constraint = AthleteConstraint(
        id=uuid4(),
        start_date=wednesday,
        end_date=wednesday,
        constraint_type="injury",
        availability="limited",
        running_allowed=False,
        cross_training_allowed=True,
    )

    result = resolve_day_availability(
        athlete=athlete,
        target_date=wednesday,
        constraints=(constraint,),
    )

    assert result.status == "limited"

    assert result.training_allowed is True
    assert result.running_allowed is False

    assert (
        result.cross_training_allowed
        is True
    )


def test_limited_day_respects_max_duration() -> None:
    athlete = create_athlete()

    friday = date(
        2026,
        8,
        28,
    )

    constraint = create_constraint(
        target_date=friday,
        availability="limited",
        max_duration_minutes=45,
    )

    result = resolve_day_availability(
        athlete=athlete,
        target_date=friday,
        constraints=(constraint,),
    )

    assert result.status == "limited"

    assert (
        result.max_duration_minutes
        == 45
    )


def test_multiple_limits_use_most_restrictive_duration() -> None:
    athlete = create_athlete()

    friday = date(
        2026,
        8,
        28,
    )

    first = create_constraint(
        target_date=friday,
        availability="limited",
        max_duration_minutes=60,
    )

    second = create_constraint(
        target_date=friday,
        availability="limited",
        max_duration_minutes=40,
    )

    result = resolve_day_availability(
        athlete=athlete,
        target_date=friday,
        constraints=(
            first,
            second,
        ),
    )

    assert (
        result.max_duration_minutes
        == 40
    )


def test_unavailable_has_priority_over_override() -> None:
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

    unavailable = create_constraint(
        target_date=thursday,
        availability="unavailable",
    )

    result = resolve_day_availability(
        athlete=athlete,
        target_date=thursday,
        constraints=(
            override,
            unavailable,
        ),
    )

    assert result.status == "unavailable"
    assert result.training_allowed is False
