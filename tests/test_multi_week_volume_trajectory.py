import pytest

from opencoach.planning.weekly.training_envelope import (
    TrainingPhase,
)
from opencoach.planning.weekly.volume_trajectory import (
    VolumeTrajectoryPhase,
    build_multi_week_volume_trajectory,
)


def test_volume_trajectory_progresses_toward_goal_demand() -> None:
    trajectory = build_multi_week_volume_trajectory(
        baseline_duration_minutes=254.0,
        goal_demand_minutes=420.0,
        phases=(
            VolumeTrajectoryPhase(
                phase=TrainingPhase.BUILD,
                weeks=3,
            ),
            VolumeTrajectoryPhase(
                phase=TrainingPhase.SPECIFIC,
                weeks=3,
            ),
        ),
    )

    assert len(trajectory.weeks) == 6

    assert (
        trajectory.weeks[0].target_duration_minutes
        > 254.0
    )

    assert (
        trajectory.weeks[-1].target_duration_minutes
        > trajectory.weeks[0].target_duration_minutes
    )

    assert all(
        week.target_duration_minutes <= 420.0
        for week in trajectory.weeks
    )


def test_recovery_week_creates_temporary_volume_drop() -> None:
    trajectory = build_multi_week_volume_trajectory(
        baseline_duration_minutes=300.0,
        goal_demand_minutes=420.0,
        phases=(
            VolumeTrajectoryPhase(
                phase=TrainingPhase.BUILD,
                weeks=4,
            ),
        ),
        recovery_every_loading_weeks=3,
        recovery_factor=0.75,
    )

    assert len(trajectory.weeks) == 4

    assert trajectory.weeks[3].recovery_week is True

    assert (
        trajectory.weeks[3].target_duration_minutes
        < trajectory.weeks[2].target_duration_minutes
    )

    assert (
        trajectory.weeks[3].progression_reference_after_minutes
        == pytest.approx(
            trajectory.weeks[2].progression_reference_after_minutes
        )
    )


def test_recovery_does_not_destroy_progression_reference() -> None:
    trajectory = build_multi_week_volume_trajectory(
        baseline_duration_minutes=300.0,
        goal_demand_minutes=420.0,
        phases=(
            VolumeTrajectoryPhase(
                phase=TrainingPhase.BUILD,
                weeks=5,
            ),
        ),
        recovery_every_loading_weeks=3,
        recovery_factor=0.75,
    )

    recovery = trajectory.weeks[3]
    following = trajectory.weeks[4]

    assert recovery.recovery_week is True

    assert (
        following.target_duration_minutes
        > recovery.target_duration_minutes
    )

    assert (
        following.progression_reference_before_minutes
        == pytest.approx(
            recovery.progression_reference_after_minutes
        )
    )


def test_goal_demand_caps_loading_progression() -> None:
    trajectory = build_multi_week_volume_trajectory(
        baseline_duration_minutes=400.0,
        goal_demand_minutes=420.0,
        phases=(
            VolumeTrajectoryPhase(
                phase=TrainingPhase.BUILD,
                weeks=5,
            ),
        ),
    )

    assert all(
        week.target_duration_minutes <= 420.0
        for week in trajectory.weeks
    )


def test_taper_is_relative_to_peak_reference() -> None:
    trajectory = build_multi_week_volume_trajectory(
        baseline_duration_minutes=300.0,
        goal_demand_minutes=420.0,
        phases=(
            VolumeTrajectoryPhase(
                phase=TrainingPhase.SPECIFIC,
                weeks=3,
            ),
            VolumeTrajectoryPhase(
                phase=TrainingPhase.TAPER,
                weeks=2,
            ),
        ),
    )

    peak = max(
        week.progression_reference_after_minutes
        for week in trajectory.weeks
        if week.phase is TrainingPhase.SPECIFIC
    )

    taper_one = trajectory.weeks[-2]
    taper_two = trajectory.weeks[-1]

    assert taper_one.phase is TrainingPhase.TAPER
    assert taper_two.phase is TrainingPhase.TAPER

    assert taper_one.target_duration_minutes == pytest.approx(
        peak * 0.75
    )

    assert taper_two.target_duration_minutes == pytest.approx(
        peak * 0.50
    )


def test_zero_baseline_remains_zero_without_safe_anchor() -> None:
    trajectory = build_multi_week_volume_trajectory(
        baseline_duration_minutes=0.0,
        goal_demand_minutes=420.0,
        phases=(
            VolumeTrajectoryPhase(
                phase=TrainingPhase.BUILD,
                weeks=3,
            ),
        ),
    )

    assert all(
        week.target_duration_minutes == 0.0
        for week in trajectory.weeks
    )


def test_recovery_is_not_inserted_immediately_before_taper() -> None:
    """Une récupération planifiée ne remplace pas le dernier pic pré-taper."""

    trajectory = build_multi_week_volume_trajectory(
        baseline_duration_minutes=254.0,
        goal_demand_minutes=420.0,
        phases=(
            VolumeTrajectoryPhase(
                phase=TrainingPhase.BASE,
                weeks=2,
            ),
            VolumeTrajectoryPhase(
                phase=TrainingPhase.BUILD,
                weeks=3,
            ),
            VolumeTrajectoryPhase(
                phase=TrainingPhase.SPECIFIC,
                weeks=3,
            ),
            VolumeTrajectoryPhase(
                phase=TrainingPhase.TAPER,
                weeks=2,
            ),
        ),
        recovery_every_loading_weeks=3,
        recovery_factor=0.75,
    )

    last_specific = trajectory.weeks[7]

    assert last_specific.phase is TrainingPhase.SPECIFIC
    assert last_specific.recovery_week is False

    assert (
        last_specific.target_duration_minutes
        >= trajectory.weeks[6].target_duration_minutes
    )


def test_goal_directed_progression_uses_required_rate_when_safe() -> None:
    """La demande de course accélère la progression si elle reste sûre."""

    trajectory = build_multi_week_volume_trajectory(
        baseline_duration_minutes=254.0,
        goal_demand_minutes=420.0,
        phases=(
            VolumeTrajectoryPhase(
                phase=TrainingPhase.BUILD,
                weeks=7,
            ),
        ),
        maximum_progression_rate=0.10,
    )

    assert (
        trajectory.weeks[-1].target_duration_minutes
        == pytest.approx(
            420.0,
            abs=1.0,
        )
    )

    assert all(
        week.target_duration_minutes <= 420.0
        for week in trajectory.weeks
    )


def test_goal_directed_progression_respects_safety_ceiling() -> None:
    """Une cible impossible ne provoque jamais une progression dangereuse."""

    trajectory = build_multi_week_volume_trajectory(
        baseline_duration_minutes=180.0,
        goal_demand_minutes=420.0,
        phases=(
            VolumeTrajectoryPhase(
                phase=TrainingPhase.BUILD,
                weeks=3,
            ),
        ),
        maximum_progression_rate=0.10,
    )

    assert (
        trajectory.weeks[0].target_duration_minutes
        == pytest.approx(198.0)
    )

    assert (
        trajectory.weeks[-1].target_duration_minutes
        < 420.0
    )


def test_70k_trajectory_builds_peak_before_taper() -> None:
    """Le scénario 70 km construit son pic avant le taper."""

    trajectory = build_multi_week_volume_trajectory(
        baseline_duration_minutes=254.0,
        goal_demand_minutes=420.0,
        phases=(
            VolumeTrajectoryPhase(
                phase=TrainingPhase.BASE,
                weeks=2,
            ),
            VolumeTrajectoryPhase(
                phase=TrainingPhase.BUILD,
                weeks=3,
            ),
            VolumeTrajectoryPhase(
                phase=TrainingPhase.SPECIFIC,
                weeks=3,
            ),
            VolumeTrajectoryPhase(
                phase=TrainingPhase.TAPER,
                weeks=2,
            ),
        ),
        maximum_progression_rate=0.10,
        recovery_every_loading_weeks=3,
        recovery_factor=0.75,
    )

    loading_weeks = tuple(
        week
        for week in trajectory.weeks
        if week.phase is not TrainingPhase.TAPER
    )

    peak_week = max(
        loading_weeks,
        key=lambda week: week.target_duration_minutes,
    )

    assert peak_week.phase is TrainingPhase.SPECIFIC
    assert peak_week.recovery_week is False

    assert (
        peak_week.target_duration_minutes
        > 360.0
    )

    assert (
        peak_week.target_duration_minutes
        <= 420.0
    )
