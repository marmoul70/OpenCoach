"""Tests de la trajectoire de développement général."""

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


def test_general_development_builds_twelve_week_trajectory() -> None:
    trajectory = build_general_development_trajectory(
        planning_date=PLANNING_DATE,
        baseline_load=400.0,
        baseline_duration_minutes=300.0,
    )

    assert trajectory.week_count == 12


def test_general_development_has_no_target_race() -> None:
    trajectory = build_general_development_trajectory(
        planning_date=PLANNING_DATE,
        baseline_load=400.0,
        baseline_duration_minutes=300.0,
    )

    assert trajectory.target_race_date is None


def test_general_development_contains_only_base_and_build() -> None:
    trajectory = build_general_development_trajectory(
        planning_date=PLANNING_DATE,
        baseline_load=400.0,
        baseline_duration_minutes=300.0,
    )

    phases = {
        week.phase
        for week in trajectory.weeks
    }

    assert phases == {
        TrainingPhase.BASE,
        TrainingPhase.BUILD,
    }


def test_general_development_never_contains_taper_week() -> None:
    trajectory = build_general_development_trajectory(
        planning_date=PLANNING_DATE,
        baseline_load=400.0,
        baseline_duration_minutes=300.0,
    )

    assert all(
        week.week_type
        is not TrajectoryWeekType.TAPER
        for week in trajectory.weeks
    )


def test_general_development_preserves_recovery_cycles() -> None:
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


def test_general_development_progresses_load() -> None:
    trajectory = build_general_development_trajectory(
        planning_date=PLANNING_DATE,
        baseline_load=400.0,
        baseline_duration_minutes=300.0,
    )

    loading_weeks = tuple(
        week
        for week in trajectory.weeks
        if (
            week.week_type
            is TrajectoryWeekType.LOADING
        )
    )

    assert loading_weeks

    assert max(
        week.progression_reference_after
        for week in loading_weeks
    ) > 400.0


def test_general_development_progresses_volume() -> None:
    trajectory = build_general_development_trajectory(
        planning_date=PLANNING_DATE,
        baseline_load=400.0,
        baseline_duration_minutes=300.0,
    )

    values = tuple(
        week.progression_reference_duration_after_minutes
        for week in trajectory.weeks
        if (
            week.progression_reference_duration_after_minutes
            is not None
        )
    )

    assert values

    assert max(values) > 300.0
