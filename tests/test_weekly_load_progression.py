import pytest

from opencoach.planning.trajectory.adjustment import (
    LoadAdjustment,
)
from opencoach.planning.weekly.load_progression import (
    LoadProgressionPolicy,
    WeeklyLoadTarget,
    calculate_weekly_load_target,
)
from opencoach.planning.weekly.training_envelope import (
    TrainingPhase,
)


def test_build_phase_increases_load() -> None:
    target = calculate_weekly_load_target(
        previous_load=100.0,
        phase=TrainingPhase.BUILD,
    )

    assert target.theoretical_load == pytest.approx(106.0)
    assert target.target_load == pytest.approx(106.0)


def test_base_progresses_more_slowly_than_build() -> None:
    base = calculate_weekly_load_target(
        previous_load=100.0,
        phase=TrainingPhase.BASE,
    )

    build = calculate_weekly_load_target(
        previous_load=100.0,
        phase=TrainingPhase.BUILD,
    )

    assert base.target_load < build.target_load


def test_specific_phase_can_stabilize_progression() -> None:
    target = calculate_weekly_load_target(
        previous_load=100.0,
        phase=TrainingPhase.SPECIFIC,
    )

    assert target.target_load == pytest.approx(102.0)


def test_taper_reduces_load() -> None:
    target = calculate_weekly_load_target(
        previous_load=100.0,
        phase=TrainingPhase.TAPER,
    )

    assert target.target_load == pytest.approx(70.0)


def test_recovery_reduces_load() -> None:
    target = calculate_weekly_load_target(
        previous_load=100.0,
        phase=TrainingPhase.RECOVERY,
    )

    assert target.target_load == pytest.approx(65.0)


def test_minor_adjustment_reduces_theoretical_target() -> None:
    target = calculate_weekly_load_target(
        previous_load=100.0,
        phase=TrainingPhase.BUILD,
        adjustment=LoadAdjustment.REDUCE_SLIGHTLY,
    )

    assert target.theoretical_load == pytest.approx(106.0)
    assert target.target_load == pytest.approx(95.4)


def test_strong_adjustment_halves_theoretical_target() -> None:
    target = calculate_weekly_load_target(
        previous_load=100.0,
        phase=TrainingPhase.BUILD,
        adjustment=LoadAdjustment.REDUCE_STRONGLY,
    )

    assert target.target_load == pytest.approx(53.0)


def test_suspension_sets_target_to_zero() -> None:
    target = calculate_weekly_load_target(
        previous_load=100.0,
        phase=TrainingPhase.BUILD,
        adjustment=LoadAdjustment.SUSPEND,
    )

    assert target.target_load == 0.0
    assert target.load_min == 0.0
    assert target.load_max == 0.0


def test_target_is_inside_allowed_range() -> None:
    target = calculate_weekly_load_target(
        previous_load=100.0,
        phase=TrainingPhase.BUILD,
    )

    assert target.load_min <= target.target_load
    assert target.target_load <= target.load_max


def test_negative_previous_load_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="précédente",
    ):
        calculate_weekly_load_target(
            previous_load=-1.0,
            phase=TrainingPhase.BASE,
        )


def test_invalid_policy_tolerance_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="tolérance basse",
    ):
        LoadProgressionPolicy(
            phase=TrainingPhase.BASE,
            progression_rate=0.04,
            tolerance_below=-0.1,
            tolerance_above=0.05,
        )


def test_weekly_target_rejects_inconsistent_range() -> None:
    with pytest.raises(
        ValueError,
        match="plage autorisée",
    ):
        WeeklyLoadTarget(
            previous_load=100.0,
            theoretical_load=105.0,
            target_load=120.0,
            load_min=90.0,
            load_max=110.0,
            phase=TrainingPhase.BASE,
            adjustment=LoadAdjustment.MAINTAIN,
        )
