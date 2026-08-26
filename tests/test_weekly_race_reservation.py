from datetime import date

from opencoach.planning.weekly.schedule_types import (
    Weekday,
)
from opencoach.planning.weekly.training_envelope_builder import (
    _exclude_reserved_race_days,
)


def test_training_race_day_is_reserved() -> None:
    available_days = (
        Weekday.MONDAY,
        Weekday.WEDNESDAY,
        Weekday.FRIDAY,
        Weekday.SUNDAY,
    )

    result = _exclude_reserved_race_days(
        week_start=date(
            2026,
            8,
            24,
        ),
        available_days=available_days,
        target_race_date=None,
        reserved_race_dates=(
            date(
                2026,
                8,
                30,
            ),
        ),
    )

    assert result == (
        Weekday.MONDAY,
        Weekday.WEDNESDAY,
        Weekday.FRIDAY,
    )


def test_future_training_race_does_not_reserve_current_week(
) -> None:
    available_days = (
        Weekday.MONDAY,
        Weekday.WEDNESDAY,
        Weekday.FRIDAY,
        Weekday.SUNDAY,
    )

    result = _exclude_reserved_race_days(
        week_start=date(
            2026,
            8,
            24,
        ),
        available_days=available_days,
        target_race_date=None,
        reserved_race_dates=(
            date(
                2026,
                9,
                13,
            ),
        ),
    )

    assert result == available_days


def test_primary_and_training_races_are_both_reserved(
) -> None:
    available_days = tuple(
        Weekday
    )

    result = _exclude_reserved_race_days(
        week_start=date(
            2026,
            8,
            24,
        ),
        available_days=available_days,
        target_race_date=date(
            2026,
            8,
            29,
        ),
        reserved_race_dates=(
            date(
                2026,
                8,
                30,
            ),
        ),
    )

    assert Weekday.SATURDAY not in result
    assert Weekday.SUNDAY not in result
