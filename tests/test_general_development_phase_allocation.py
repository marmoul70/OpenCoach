"""Tests de périodisation du mode Maintenance."""

from datetime import date, timedelta

from opencoach.coaching.replanning import (
    GeneralDevelopmentPolicy,
    allocate_general_development_phases,
)
from opencoach.planning.weekly.training_envelope import (
    TrainingPhase,
)


PLANNING_DATE = date(
    2026,
    8,
    24,
)


def test_default_maintenance_covers_twelve_weeks() -> None:
    allocation = allocate_general_development_phases(
        planning_date=PLANNING_DATE,
    )

    assert allocation.total_weeks == 12

    assert allocation.start_date == PLANNING_DATE

    assert allocation.end_date == (
        PLANNING_DATE
        + timedelta(weeks=12)
        - timedelta(days=1)
    )


def test_maintenance_uses_single_base_phase_temporarily() -> None:
    allocation = allocate_general_development_phases(
        planning_date=PLANNING_DATE,
    )

    assert len(
        allocation.phases
    ) == 1

    phase = allocation.phases[0]

    assert phase.phase is TrainingPhase.BASE

    assert phase.allocated_weeks == 12


def test_maintenance_never_contains_build() -> None:
    allocation = allocate_general_development_phases(
        planning_date=PLANNING_DATE,
    )

    assert all(
        phase.phase
        is not TrainingPhase.BUILD
        for phase in allocation.phases
    )


def test_maintenance_never_contains_specific() -> None:
    allocation = allocate_general_development_phases(
        planning_date=PLANNING_DATE,
    )

    assert all(
        phase.phase
        is not TrainingPhase.SPECIFIC
        for phase in allocation.phases
    )


def test_maintenance_never_contains_taper() -> None:
    allocation = allocate_general_development_phases(
        planning_date=PLANNING_DATE,
    )

    assert all(
        phase.phase
        is not TrainingPhase.TAPER
        for phase in allocation.phases
    )


def test_custom_policy_controls_cycle_duration() -> None:
    policy = GeneralDevelopmentPolicy(
        maintenance_weeks=8,
    )

    allocation = allocate_general_development_phases(
        planning_date=PLANNING_DATE,
        policy=policy,
    )

    assert allocation.total_weeks == 8

    assert allocation.phases[0].allocated_weeks == 8
