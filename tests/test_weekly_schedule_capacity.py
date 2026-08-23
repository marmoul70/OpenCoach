from datetime import date

import pytest

from opencoach.planning.athlete.availability import (
    DayAvailability,
)
from opencoach.planning.athlete.weekly_availability import (
    WeeklyAvailability,
)
from opencoach.planning.weekly.schedule_capacity import (
    DayScheduleCapacity,
    build_day_schedule_capacities,
)
from opencoach.planning.weekly.schedule_types import (
    Weekday,
)


def test_capacity_without_limit_accepts_any_duration() -> None:
    capacity = DayScheduleCapacity(
        day=Weekday.MONDAY,
    )

    assert capacity.can_fit(
        minimum_duration_minutes=180,
    )


def test_capacity_accepts_duration_equal_to_limit() -> None:
    capacity = DayScheduleCapacity(
        day=Weekday.MONDAY,
        max_duration_minutes=60,
    )

    assert capacity.can_fit(
        minimum_duration_minutes=60,
    )


def test_capacity_rejects_duration_above_limit() -> None:
    capacity = DayScheduleCapacity(
        day=Weekday.MONDAY,
        max_duration_minutes=45,
    )

    assert (
        capacity.can_fit(
            minimum_duration_minutes=60,
        )
        is False
    )


def test_invalid_duration_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="strictement positive",
    ):
        DayScheduleCapacity(
            day=Weekday.MONDAY,
            max_duration_minutes=0,
        )


def test_weekly_availability_is_converted_to_capacities() -> None:
    weekly = WeeklyAvailability(
        start_date=date(2027, 3, 1),
        end_date=date(2027, 3, 7),
        days=(
            DayAvailability(
                date=date(2027, 3, 1),
                preferred=True,
                status="preferred",
                training_allowed=True,
                requires_confirmation=False,
                running_allowed=True,
                cross_training_allowed=True,
                max_duration_minutes=60,
                constraints=(),
            ),
            DayAvailability(
                date=date(2027, 3, 2),
                preferred=False,
                status="unavailable",
                training_allowed=False,
                requires_confirmation=False,
                running_allowed=False,
                cross_training_allowed=False,
                max_duration_minutes=None,
                constraints=(),
            ),
            DayAvailability(
                date=date(2027, 3, 7),
                preferred=True,
                status="limited",
                training_allowed=True,
                requires_confirmation=False,
                running_allowed=True,
                cross_training_allowed=True,
                max_duration_minutes=180,
                constraints=(),
            ),
        ),
    )

    capacities = (
        build_day_schedule_capacities(
            weekly_availability=weekly,
        )
    )

    assert capacities == (
        DayScheduleCapacity(
            day=Weekday.MONDAY,
            max_duration_minutes=60,
        ),
        DayScheduleCapacity(
            day=Weekday.SUNDAY,
            max_duration_minutes=180,
        ),
    )


def test_unavailable_day_is_not_converted() -> None:
    weekly = WeeklyAvailability(
        start_date=date(2027, 3, 1),
        end_date=date(2027, 3, 7),
        days=(
            DayAvailability(
                date=date(2027, 3, 1),
                preferred=True,
                status="unavailable",
                training_allowed=False,
                requires_confirmation=False,
                running_allowed=False,
                cross_training_allowed=False,
                max_duration_minutes=None,
                constraints=(),
            ),
        ),
    )

    assert (
        build_day_schedule_capacities(
            weekly_availability=weekly,
        )
        == ()
    )
