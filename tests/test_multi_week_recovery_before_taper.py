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
