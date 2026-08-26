from datetime import date

from opencoach.planning.stimulus.training import (
    StimulusLoadCategory,
)
from opencoach.planning.weekly.schedule_capacity import (
    DayScheduleCapacity,
)
from opencoach.planning.weekly.schedule_types import (
    Weekday,
)
from opencoach.planning.weekly.training_envelope_builder import (
    _apply_post_race_recovery,
    _build_post_race_recovery_stages,
)


RECOVERY_DATES = (
    date(2026, 9, 7),
    date(2026, 9, 8),
    date(2026, 9, 9),
    date(2026, 9, 10),
    date(2026, 9, 11),
    date(2026, 9, 12),
)


def _capacities():
    return _apply_post_race_recovery(
        week_start=date(
            2026,
            9,
            7,
        ),
        available_days=(
            Weekday.MONDAY,
            Weekday.TUESDAY,
            Weekday.WEDNESDAY,
            Weekday.THURSDAY,
            Weekday.FRIDAY,
            Weekday.SATURDAY,
            Weekday.SUNDAY,
        ),
        day_capacities=(),
        recovery_dates=RECOVERY_DATES,
    )


def test_j1_j2_allow_support_only() -> None:
    by_day = {
        capacity.day: capacity
        for capacity in _capacities()
    }

    for day in (
        Weekday.MONDAY,
        Weekday.TUESDAY,
    ):
        capacity = by_day[
            day
        ]

        assert (
            capacity.max_duration_minutes
            == 30
        )

        assert capacity.allows_load_category(
            StimulusLoadCategory.SUPPORT
        )

        assert not capacity.allows_load_category(
            StimulusLoadCategory.ENDURANCE
        )

        assert not capacity.allows_load_category(
            StimulusLoadCategory.QUALITY
        )

        assert not capacity.allows_load_category(
            StimulusLoadCategory.STRENGTH
        )


def test_j3_j4_allow_easy_endurance() -> None:
    by_day = {
        capacity.day: capacity
        for capacity in _capacities()
    }

    for day in (
        Weekday.WEDNESDAY,
        Weekday.THURSDAY,
    ):
        capacity = by_day[
            day
        ]

        assert (
            capacity.max_duration_minutes
            == 45
        )

        assert capacity.allows_load_category(
            StimulusLoadCategory.SUPPORT
        )

        assert capacity.allows_load_category(
            StimulusLoadCategory.ENDURANCE
        )

        assert not capacity.allows_load_category(
            StimulusLoadCategory.QUALITY
        )

        assert not capacity.allows_load_category(
            StimulusLoadCategory.STRENGTH
        )


def test_j5_j6_allow_controlled_endurance() -> None:
    by_day = {
        capacity.day: capacity
        for capacity in _capacities()
    }

    for day in (
        Weekday.FRIDAY,
        Weekday.SATURDAY,
    ):
        capacity = by_day[
            day
        ]

        assert (
            capacity.max_duration_minutes
            == 60
        )

        assert capacity.allows_load_category(
            StimulusLoadCategory.SUPPORT
        )

        assert capacity.allows_load_category(
            StimulusLoadCategory.ENDURANCE
        )

        assert not capacity.allows_load_category(
            StimulusLoadCategory.QUALITY
        )

        assert not capacity.allows_load_category(
            StimulusLoadCategory.STRENGTH
        )


def test_j7_returns_to_normal_capacity() -> None:
    by_day = {
        capacity.day: capacity
        for capacity in _capacities()
    }

    sunday = by_day[
        Weekday.SUNDAY
    ]

    assert (
        sunday.max_duration_minutes
        is None
    )

    assert sunday.allows_load_category(
        StimulusLoadCategory.SUPPORT
    )

    assert sunday.allows_load_category(
        StimulusLoadCategory.ENDURANCE
    )

    assert sunday.allows_load_category(
        StimulusLoadCategory.QUALITY
    )

    assert sunday.allows_load_category(
        StimulusLoadCategory.STRENGTH
    )


def test_recovery_never_increases_athlete_capacity() -> None:
    capacities = _apply_post_race_recovery(
        week_start=date(
            2026,
            9,
            7,
        ),
        available_days=(
            Weekday.FRIDAY,
        ),
        day_capacities=(
            DayScheduleCapacity(
                day=Weekday.FRIDAY,
                max_duration_minutes=35,
            ),
        ),
        recovery_dates=RECOVERY_DATES,
    )

    assert (
        capacities[0].max_duration_minutes
        == 35
    )


def test_separate_recovery_windows_restart_at_j1() -> None:
    stages = (
        _build_post_race_recovery_stages(
            (
                date(2026, 9, 7),
                date(2026, 9, 8),
                date(2026, 9, 12),
                date(2026, 9, 13),
            )
        )
    )

    assert stages == {
        date(2026, 9, 7): 1,
        date(2026, 9, 8): 2,
        date(2026, 9, 12): 1,
        date(2026, 9, 13): 2,
    }
