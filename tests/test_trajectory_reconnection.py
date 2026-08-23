import pytest

from opencoach.planning.trajectory.reconnection import (
    ReconnectionStatus,
    TrajectoryReconnectionPolicy,
    calculate_trajectory_reconnection,
)


def test_large_gap_starts_reconnection() -> None:
    result = calculate_trajectory_reconnection(
        observed_load=350.0,
        structural_reference_load=459.25,
    )

    assert result.status is ReconnectionStatus.ACTIVE

    assert result.target_load == pytest.approx(
        385.0
    )

    assert result.increase_rate == pytest.approx(
        0.10
    )

    assert result.structural_reference_reached is False


def test_reconnection_never_exceeds_structural_reference() -> None:
    result = calculate_trajectory_reconnection(
        observed_load=440.0,
        structural_reference_load=459.25,
    )

    assert result.target_load == pytest.approx(
        459.25
    )

    assert result.structural_reference_reached is True


def test_small_gap_completes_reconnection() -> None:
    result = calculate_trajectory_reconnection(
        observed_load=440.0,
        structural_reference_load=459.25,
    )

    assert result.status is ReconnectionStatus.COMPLETED

    assert result.target_load == pytest.approx(
        459.25
    )

    assert result.gap_after == 0.0


def test_observed_load_above_reference_needs_no_reconnection() -> None:
    result = calculate_trajectory_reconnection(
        observed_load=500.0,
        structural_reference_load=459.25,
    )

    assert result.status is ReconnectionStatus.NOT_REQUIRED

    assert result.target_load == pytest.approx(
        459.25
    )

    assert result.structural_reference_reached is True


def test_zero_structural_reference_needs_no_reconnection() -> None:
    result = calculate_trajectory_reconnection(
        observed_load=0.0,
        structural_reference_load=0.0,
    )

    assert result.status is ReconnectionStatus.NOT_REQUIRED

    assert result.target_load == 0.0


def test_zero_observed_load_does_not_invent_relative_progression() -> None:
    result = calculate_trajectory_reconnection(
        observed_load=0.0,
        structural_reference_load=400.0,
    )

    assert result.status is ReconnectionStatus.ACTIVE

    assert result.target_load == 0.0

    assert result.structural_reference_reached is False


def test_custom_progression_policy_is_supported() -> None:
    policy = TrajectoryReconnectionPolicy(
        maximum_weekly_increase=0.05,
    )

    result = calculate_trajectory_reconnection(
        observed_load=350.0,
        structural_reference_load=500.0,
        policy=policy,
    )

    assert result.target_load == pytest.approx(
        367.5
    )

    assert result.increase_rate == pytest.approx(
        0.05
    )


def test_exact_reference_needs_no_reconnection() -> None:
    result = calculate_trajectory_reconnection(
        observed_load=459.25,
        structural_reference_load=459.25,
    )

    assert result.status is ReconnectionStatus.NOT_REQUIRED

    assert result.target_load == pytest.approx(
        459.25
    )


def test_negative_observed_load_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="observée",
    ):
        calculate_trajectory_reconnection(
            observed_load=-1.0,
            structural_reference_load=400.0,
        )


def test_negative_structural_reference_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="structurelle",
    ):
        calculate_trajectory_reconnection(
            observed_load=300.0,
            structural_reference_load=-1.0,
        )


def test_negative_maximum_progression_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="progression maximale",
    ):
        TrajectoryReconnectionPolicy(
            maximum_weekly_increase=-0.01,
        )


def test_invalid_completion_tolerance_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="tolérance",
    ):
        TrajectoryReconnectionPolicy(
            completion_tolerance=1.1,
        )
