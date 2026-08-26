"""Tests de la trajectoire Maintenance."""

from datetime import date

from opencoach.coaching.replanning import (
    build_general_development_trajectory,
)
from opencoach.planning.trajectory.multi_week import (
    TrajectoryWeekType,
)
from opencoach.planning.weekly.training_envelope import (
    TrainingPhase,
)


PLANNING_DATE = date(
    2026,
    8,
    24,
)


def test_maintenance_builds_twelve_week_trajectory() -> None:
    trajectory = build_general_development_trajectory(
        planning_date=PLANNING_DATE,
        baseline_load=400.0,
        baseline_duration_minutes=300.0,
    )

    assert trajectory.week_count == 12


def test_maintenance_has_no_target_race() -> None:
    trajectory = build_general_development_trajectory(
        planning_date=PLANNING_DATE,
        baseline_load=400.0,
        baseline_duration_minutes=300.0,
    )

    assert trajectory.target_race_date is None


def test_maintenance_never_enters_build_specific_or_taper() -> None:
    trajectory = build_general_development_trajectory(
        planning_date=PLANNING_DATE,
        baseline_load=400.0,
        baseline_duration_minutes=300.0,
    )

    assert all(
        week.phase
        is TrainingPhase.BASE
        for week in trajectory.weeks
    )


def test_maintenance_contains_recovery_weeks() -> None:
    trajectory = build_general_development_trajectory(
        planning_date=PLANNING_DATE,
        baseline_load=400.0,
        baseline_duration_minutes=300.0,
    )

    assert any(
        week.week_type
        is TrajectoryWeekType.RECOVERY
        for week in trajectory.weeks
    )


def test_maintenance_load_does_not_build_indefinitely() -> None:
    trajectory = build_general_development_trajectory(
        planning_date=PLANNING_DATE,
        baseline_load=400.0,
        baseline_duration_minutes=300.0,
    )

    targets = tuple(
        week.target_load
        for week in trajectory.weeks
    )

    assert targets

    assert max(targets) <= 440.0


def test_maintenance_volume_does_not_build_indefinitely() -> None:
    trajectory = build_general_development_trajectory(
        planning_date=PLANNING_DATE,
        baseline_load=400.0,
        baseline_duration_minutes=300.0,
    )

    values = tuple(
        week.target_duration_minutes
        for week in trajectory.weeks
        if week.target_duration_minutes
        is not None
    )

    assert values

    assert max(values) <= 330.0
