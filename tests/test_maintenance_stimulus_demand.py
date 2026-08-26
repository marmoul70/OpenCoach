"""Tests de densité des stimuli en mode Maintenance."""

from opencoach.planning.stimulus.contextual_prescription import (
    build_contextual_stimulus_prescription,
)
from opencoach.planning.stimulus.training import (
    StimulusPriority,
)
from opencoach.planning.stimulus.weekly_demand import (
    StimulusDemandDensity,
    build_weekly_stimulus_demand,
)
from opencoach.planning.trajectory.multi_week import (
    TrajectoryWeekType,
)
from opencoach.planning.weekly.training_envelope import (
    TrainingPhase,
)


def _prescription():
    return build_contextual_stimulus_prescription(
        phase=TrainingPhase.BASE,
        race_profile=None,
        phase_week_index=1,
    )


def test_moderate_maintenance_limits_quality() -> None:
    demand = build_weekly_stimulus_demand(
        prescription=_prescription(),
        week_type=TrajectoryWeekType.LOADING,
        target_load=380.0,
        reference_load=400.0,
        maintenance_mode=True,
    )

    assert (
        demand.maximum_quality_exposures
        == 1
    )


def test_moderate_maintenance_makes_key_work_optional() -> None:
    demand = build_weekly_stimulus_demand(
        prescription=_prescription(),
        week_type=TrajectoryWeekType.LOADING,
        target_load=380.0,
        reference_load=400.0,
        maintenance_mode=True,
    )

    key_demands = tuple(
        item
        for item in demand.demands
        if (
            item.requirement.priority
            is StimulusPriority.KEY
        )
    )

    assert key_demands

    assert all(
        item.minimum_occurrences == 0
        for item in key_demands
    )


def test_high_maintenance_allows_more_quality() -> None:
    demand = build_weekly_stimulus_demand(
        prescription=_prescription(),
        week_type=TrajectoryWeekType.LOADING,
        target_load=420.0,
        reference_load=400.0,
        maintenance_mode=True,
    )

    assert (
        demand.maximum_quality_exposures
        == 2
    )

    key_demands = tuple(
        item
        for item in demand.demands
        if (
            item.requirement.priority
            is StimulusPriority.KEY
        )
    )

    assert key_demands

    assert any(
        item.minimum_occurrences == 1
        for item in key_demands
    )


def test_neutral_maintenance_keeps_single_quality_exposure() -> None:
    demand = build_weekly_stimulus_demand(
        prescription=_prescription(),
        week_type=TrajectoryWeekType.LOADING,
        target_load=400.0,
        reference_load=400.0,
        maintenance_mode=True,
    )

    assert (
        demand.maximum_quality_exposures
        == 1
    )


def test_low_maintenance_uses_recovery_rules() -> None:
    demand = build_weekly_stimulus_demand(
        prescription=_prescription(),
        week_type=TrajectoryWeekType.RECOVERY,
        target_load=320.0,
        reference_load=400.0,
        maintenance_mode=True,
    )

    assert (
        demand.density
        is StimulusDemandDensity.LOW
    )

    assert (
        demand.maximum_quality_exposures
        == 1
    )


def test_moderate_maintenance_uses_moderate_density() -> None:
    demand = build_weekly_stimulus_demand(
        prescription=_prescription(),
        week_type=TrajectoryWeekType.LOADING,
        target_load=400.0,
        reference_load=400.0,
        maintenance_mode=True,
    )

    assert (
        demand.density
        is StimulusDemandDensity.MODERATE
    )

    assert (
        demand.maximum_key_exposures
        == 1
    )


def test_high_maintenance_uses_high_density() -> None:
    demand = build_weekly_stimulus_demand(
        prescription=_prescription(),
        week_type=TrajectoryWeekType.LOADING,
        target_load=420.0,
        reference_load=400.0,
        maintenance_mode=True,
    )

    assert (
        demand.density
        is StimulusDemandDensity.HIGH
    )

    assert (
        demand.maximum_key_exposures
        == 2
    )


def test_below_baseline_maintenance_limits_key_exposures() -> None:
    demand = build_weekly_stimulus_demand(
        prescription=_prescription(),
        week_type=TrajectoryWeekType.LOADING,
        target_load=380.0,
        reference_load=400.0,
        maintenance_mode=True,
    )

    assert (
        demand.density
        is StimulusDemandDensity.MODERATE
    )

    assert (
        demand.maximum_key_exposures
        == 1
    )
