"""Tests de périodisation du développement général."""

from datetime import date, timedelta

import pytest

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


def test_default_general_development_covers_twelve_weeks() -> None:
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


def test_general_development_contains_base_then_build() -> None:
    allocation = allocate_general_development_phases(
        planning_date=PLANNING_DATE,
    )

    assert tuple(
        phase.phase
        for phase in allocation.phases
    ) == (
        TrainingPhase.BASE,
        TrainingPhase.BUILD,
    )


def test_general_development_never_contains_taper() -> None:
    allocation = allocate_general_development_phases(
        planning_date=PLANNING_DATE,
    )

    assert all(
        phase.phase
        is not TrainingPhase.TAPER
        for phase in allocation.phases
    )


def test_general_development_never_contains_specific() -> None:
    allocation = allocate_general_development_phases(
        planning_date=PLANNING_DATE,
    )

    assert all(
        phase.phase
        is not TrainingPhase.SPECIFIC
        for phase in allocation.phases
    )


def test_default_policy_uses_six_base_and_six_build_weeks() -> None:
    allocation = allocate_general_development_phases(
        planning_date=PLANNING_DATE,
    )

    base, build = allocation.phases

    assert base.phase is TrainingPhase.BASE
    assert base.allocated_weeks == 6

    assert build.phase is TrainingPhase.BUILD
    assert build.allocated_weeks == 6


def test_custom_policy_controls_phase_duration() -> None:
    policy = GeneralDevelopmentPolicy(
        base_weeks=4,
        build_weeks=8,
    )

    allocation = allocate_general_development_phases(
        planning_date=PLANNING_DATE,
        policy=policy,
    )

    assert allocation.total_weeks == 12

    assert allocation.phases[0].allocated_weeks == 4
    assert allocation.phases[1].allocated_weeks == 8


@pytest.mark.parametrize(
    (
        "base_weeks",
        "build_weeks",
    ),
    [
        (0, 6),
        (6, 0),
        (-1, 6),
        (6, -1),
    ],
)
def test_policy_rejects_non_positive_phase_duration(
    base_weeks: int,
    build_weeks: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="strictement positive",
    ):
        GeneralDevelopmentPolicy(
            base_weeks=base_weeks,
            build_weeks=build_weeks,
        )


def test_phase_dates_are_contiguous() -> None:
    allocation = allocate_general_development_phases(
        planning_date=PLANNING_DATE,
    )

    base, build = allocation.phases

    assert (
        build.start_date
        == base.end_date + timedelta(days=1)
    )
