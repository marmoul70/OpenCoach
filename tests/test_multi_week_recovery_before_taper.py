"""Tests de coordination entre récupération planifiée et taper."""

from datetime import date

from opencoach.planning.trajectory.multi_week import (
    TrajectoryWeekType,
)
from opencoach.planning.trajectory.multi_week_builder import (
    build_multi_week_trajectory,
)


def test_planned_recovery_is_not_inserted_immediately_before_taper() -> None:
    """Le taper suivant fournit déjà la décharge planifiée."""

    trajectory = build_multi_week_trajectory(
        planning_date=date(2026, 6, 15),
        target_race_date=date(2026, 9, 13),
        baseline_load=130.18,
    )

    weeks = trajectory.weeks

    taper_index = next(
        index
        for index, week in enumerate(weeks)
        if week.week_type
        is TrajectoryWeekType.TAPER
    )

    assert taper_index > 0

    previous_week = weeks[
        taper_index - 1
    ]

    assert (
        previous_week.week_type
        is not TrajectoryWeekType.RECOVERY
    )


def test_specific_week_before_taper_remains_loading_week() -> None:
    """La dernière semaine spécifique reste productive avant taper."""

    trajectory = build_multi_week_trajectory(
        planning_date=date(2026, 6, 15),
        target_race_date=date(2026, 9, 13),
        baseline_load=130.18,
    )

    week = next(
        week
        for week in trajectory.weeks
        if week.week_start
        == date(2026, 8, 24)
    )

    assert (
        week.week_type
        is TrajectoryWeekType.LOADING
    )
def test_short_specific_phase_preserves_two_loading_weeks() -> None:
    """Une phase spécifique courte ne doit pas être consommée par
    une récupération périodique planifiée.
    """

    trajectory = build_multi_week_trajectory(
        planning_date=date(2026, 6, 15),
        target_race_date=date(2026, 8, 23),
        baseline_load=100.0,
        baseline_duration_minutes=254.0,
        goal_duration_demand_minutes=420.0,
    )

    specific_weeks = tuple(
        week
        for week in trajectory.weeks
        if week.phase.value == "specific"
    )

    assert len(specific_weeks) == 2

    assert all(
        week.week_type
        is TrajectoryWeekType.LOADING
        for week in specific_weeks
    )


def test_specific_phase_can_recover_when_two_loading_weeks_remain() -> None:
    """Une récupération reste possible dans une phase spécifique
    suffisamment longue.
    """

    trajectory = build_multi_week_trajectory(
        planning_date=date(2026, 6, 15),
        target_race_date=date(2026, 9, 13),
        baseline_load=100.0,
    )

    specific_weeks = tuple(
        week
        for week in trajectory.weeks
        if week.phase.value == "specific"
    )

    recovery_indexes = tuple(
        index
        for index, week in enumerate(specific_weeks)
        if week.week_type
        is TrajectoryWeekType.RECOVERY
    )

    for recovery_index in recovery_indexes:
        loading_after = sum(
            1
            for week in specific_weeks[
                recovery_index + 1:
            ]
            if week.week_type
            is TrajectoryWeekType.LOADING
        )

        assert loading_after >= 2