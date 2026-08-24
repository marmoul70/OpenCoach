import pytest

from datetime import date

from opencoach.planning.trajectory.multi_week import (
    TrajectoryWeekType,
)
from opencoach.planning.trajectory.multi_week_builder import (
    build_multi_week_trajectory,
)
from opencoach.planning.weekly.training_envelope import (
    TrainingPhase,
)


PLANNING_DATE = date(2027, 1, 4)
RACE_DATE = date(2027, 3, 22)


def test_volume_trajectory_remains_optional() -> None:
    """Le builder reste compatible sans données temporelles."""

    trajectory = build_multi_week_trajectory(
        planning_date=PLANNING_DATE,
        target_race_date=RACE_DATE,
        baseline_load=400.0,
    )

    assert all(
        week.target_duration_minutes is None
        for week in trajectory.weeks
    )


def test_builder_populates_weekly_volume_trajectory() -> None:
    """Le builder construit charge et volume sur les mêmes semaines."""

    trajectory = build_multi_week_trajectory(
        planning_date=PLANNING_DATE,
        target_race_date=RACE_DATE,
        baseline_load=400.0,
        baseline_duration_minutes=254.0,
        goal_duration_demand_minutes=420.0,
    )

    assert trajectory.week_count == 11

    assert all(
        week.previous_duration_minutes is not None
        for week in trajectory.weeks
    )

    assert all(
        week.progression_reference_duration_before_minutes
        is not None
        for week in trajectory.weeks
    )

    assert all(
        week.progression_reference_duration_after_minutes
        is not None
        for week in trajectory.weeks
    )

    assert all(
        week.target_duration_minutes is not None
        for week in trajectory.weeks
    )

    loading_targets = (
        week.target_duration_minutes
        for week in trajectory.weeks
        if (
            week.week_type
            is TrajectoryWeekType.LOADING
        )
    )

    assert all(
        target <= 420.0
        for target in loading_targets
    )


def test_volume_recovery_uses_same_recovery_weeks_as_load() -> None:
    """Charge et volume partagent la décision de récupération."""

    trajectory = build_multi_week_trajectory(
        planning_date=PLANNING_DATE,
        target_race_date=RACE_DATE,
        baseline_load=400.0,
        baseline_duration_minutes=254.0,
        goal_duration_demand_minutes=420.0,
    )

    recovery_weeks = tuple(
        week
        for week in trajectory.weeks
        if (
            week.week_type
            is TrajectoryWeekType.RECOVERY
        )
    )

    assert recovery_weeks

    for week in recovery_weeks:
        assert (
            week.target_duration_minutes
            < week.progression_reference_duration_before_minutes
        )

        assert (
            week.progression_reference_duration_after_minutes
            == pytest.approx(
                week.progression_reference_duration_before_minutes
            )
        )


def test_two_week_taper_is_relative_to_volume_peak() -> None:
    """Le taper horaire utilise 75 puis 50 % du pic construit."""

    trajectory = build_multi_week_trajectory(
        planning_date=PLANNING_DATE,
        target_race_date=RACE_DATE,
        baseline_load=400.0,
        baseline_duration_minutes=254.0,
        goal_duration_demand_minutes=420.0,
    )

    taper_weeks = tuple(
        week
        for week in trajectory.weeks
        if week.phase is TrainingPhase.TAPER
    )

    assert len(taper_weeks) == 2

    peak_reference = (
        taper_weeks[0]
        .progression_reference_duration_before_minutes
    )

    assert taper_weeks[0].target_duration_minutes == pytest.approx(
        peak_reference * 0.75
    )

    assert taper_weeks[1].target_duration_minutes == pytest.approx(
        peak_reference * 0.50
    )

    assert (
        taper_weeks[0]
        .progression_reference_duration_after_minutes
        == pytest.approx(peak_reference)
    )

    assert (
        taper_weeks[1]
        .progression_reference_duration_after_minutes
        == pytest.approx(peak_reference)
    )
