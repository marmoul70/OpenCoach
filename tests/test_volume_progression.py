import pytest

from opencoach.planning.weekly.training_envelope import (
    TrainingPhase,
)
from opencoach.planning.weekly.volume_progression import (
    VolumeProgressionPolicy,
    calculate_weekly_volume_target,
)


def test_build_progresses_weekly_volume() -> None:
    result = calculate_weekly_volume_target(
        previous_duration_minutes=300.0,
        phase=TrainingPhase.BUILD,
    )

    assert result.previous_duration_minutes == 300.0
    assert result.theoretical_duration_minutes == pytest.approx(
        318.0
    )
    assert result.target_duration_minutes == pytest.approx(
        318.0
    )


def test_specific_can_continue_volume_progression() -> None:
    result = calculate_weekly_volume_target(
        previous_duration_minutes=360.0,
        phase=TrainingPhase.SPECIFIC,
    )

    assert result.target_duration_minutes == pytest.approx(
        374.4
    )


def test_recovery_reduces_volume_without_destroying_reference() -> None:
    result = calculate_weekly_volume_target(
        previous_duration_minutes=360.0,
        phase=TrainingPhase.RECOVERY,
    )

    assert result.target_duration_minutes == pytest.approx(
        270.0
    )

    assert result.previous_duration_minutes == 360.0


def test_taper_reduces_volume() -> None:
    result = calculate_weekly_volume_target(
        previous_duration_minutes=360.0,
        phase=TrainingPhase.TAPER,
    )

    assert result.target_duration_minutes == pytest.approx(
        270.0
    )


def test_zero_volume_remains_zero() -> None:
    result = calculate_weekly_volume_target(
        previous_duration_minutes=0.0,
        phase=TrainingPhase.BASE,
    )

    assert result.target_duration_minutes == 0.0


def test_negative_previous_duration_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="durée hebdomadaire précédente",
    ):
        calculate_weekly_volume_target(
            previous_duration_minutes=-1.0,
            phase=TrainingPhase.BUILD,
        )


def test_policy_rejects_progression_below_minus_one() -> None:
    with pytest.raises(ValueError):
        VolumeProgressionPolicy(
            phase=TrainingPhase.BUILD,
            progression_rate=-1.01,
        )


def test_positive_progression_is_capped_by_maximum_rate() -> None:
    policies = {
        TrainingPhase.BUILD: VolumeProgressionPolicy(
            phase=TrainingPhase.BUILD,
            progression_rate=0.20,
        ),
    }

    result = calculate_weekly_volume_target(
        previous_duration_minutes=300.0,
        phase=TrainingPhase.BUILD,
        maximum_progression_rate=0.10,
        policies=policies,
    )

    assert result.theoretical_duration_minutes == pytest.approx(
        360.0
    )

    assert result.target_duration_minutes == pytest.approx(
        330.0
    )

    assert result.progression_limited is True


def test_normal_progression_is_not_marked_as_limited() -> None:
    result = calculate_weekly_volume_target(
        previous_duration_minutes=300.0,
        phase=TrainingPhase.BUILD,
        maximum_progression_rate=0.10,
    )

    assert result.target_duration_minutes == pytest.approx(
        318.0
    )

    assert result.progression_limited is False


def test_goal_demand_is_reachable_within_progression_ceiling() -> None:
    result = calculate_weekly_volume_target(
        previous_duration_minutes=240.0,
        phase=TrainingPhase.BUILD,
        maximum_progression_rate=0.10,
        goal_demand_minutes=330.0,
        weeks_remaining=4,
    )

    assert (
        result.reachable_duration_ceiling_minutes
        == pytest.approx(
            351.384
        )
    )

    assert result.goal_demand_reachable is True


def test_goal_demand_can_be_unreachable() -> None:
    result = calculate_weekly_volume_target(
        previous_duration_minutes=240.0,
        phase=TrainingPhase.BUILD,
        maximum_progression_rate=0.10,
        goal_demand_minutes=420.0,
        weeks_remaining=4,
    )

    assert (
        result.reachable_duration_ceiling_minutes
        == pytest.approx(
            351.384
        )
    )

    assert result.goal_demand_reachable is False


def test_goal_reachability_is_unknown_without_goal_demand() -> None:
    result = calculate_weekly_volume_target(
        previous_duration_minutes=300.0,
        phase=TrainingPhase.BUILD,
    )

    assert result.goal_demand_minutes is None
    assert result.goal_demand_reachable is None


def test_goal_demand_requires_weeks_remaining() -> None:
    with pytest.raises(
        ValueError,
        match="semaines restantes",
    ):
        calculate_weekly_volume_target(
            previous_duration_minutes=300.0,
            phase=TrainingPhase.BUILD,
            goal_demand_minutes=420.0,
        )


def test_negative_goal_demand_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="demande de volume",
    ):
        calculate_weekly_volume_target(
            previous_duration_minutes=300.0,
            phase=TrainingPhase.BUILD,
            goal_demand_minutes=-1.0,
            weeks_remaining=4,
        )


def test_negative_weeks_remaining_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="semaines restantes",
    ):
        calculate_weekly_volume_target(
            previous_duration_minutes=300.0,
            phase=TrainingPhase.BUILD,
            goal_demand_minutes=420.0,
            weeks_remaining=-1,
        )


def test_70k_goal_demand_is_assessed_against_reachable_progression() -> None:
    result = calculate_weekly_volume_target(
        previous_duration_minutes=254.0,
        phase=TrainingPhase.SPECIFIC,
        maximum_progression_rate=0.10,
        goal_demand_minutes=420.0,
        weeks_remaining=3,
    )

    assert (
        result.reachable_duration_ceiling_minutes
        == pytest.approx(
            338.074
        )
    )

    assert result.goal_demand_reachable is False
