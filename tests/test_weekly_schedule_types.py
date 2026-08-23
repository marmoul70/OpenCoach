from opencoach.planning.weekly_schedule_types import (
    FatigueBudget,
    Weekday,
)


def test_weekday_values_are_stable() -> None:
    assert Weekday.MONDAY.value == "monday"
    assert Weekday.TUESDAY.value == "tuesday"
    assert Weekday.WEDNESDAY.value == "wednesday"
    assert Weekday.THURSDAY.value == "thursday"
    assert Weekday.FRIDAY.value == "friday"
    assert Weekday.SATURDAY.value == "saturday"
    assert Weekday.SUNDAY.value == "sunday"


def test_fatigue_budget_values_are_stable() -> None:
    assert FatigueBudget.LOW.value == "low"
    assert FatigueBudget.MODERATE.value == "moderate"
    assert FatigueBudget.HIGH.value == "high"