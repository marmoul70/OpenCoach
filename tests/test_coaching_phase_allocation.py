from datetime import date

import pytest

from opencoach.planning.trajectory.coaching_phase_allocation import (
    AllocatedTrainingPhase,
    CoachingPhaseAllocation,
    PhaseDurationPolicy,
    allocate_coaching_phases,
)
from opencoach.planning.weekly.training_envelope import (
    TrainingPhase,
)


def test_long_horizon_reaches_preferred_phase_lengths() -> None:
    allocation = allocate_coaching_phases(
        planning_date=date(
            2027,
            1,
            1,
        ),
        target_race_date=date(
            2027,
            4,
            16,
        ),
    )

    lengths = {
        phase.phase: phase.allocated_weeks
        for phase in allocation.phases
    }

    assert lengths[
        TrainingPhase.BASE
    ] >= 5

    assert lengths[
        TrainingPhase.BUILD
    ] >= 4

    assert lengths[
        TrainingPhase.SPECIFIC
    ] >= 4

    assert lengths[
        TrainingPhase.TAPER
    ] >= 2


def test_shorter_horizon_compresses_phases() -> None:
    allocation = allocate_coaching_phases(
        planning_date=date(
            2027,
            3,
            1,
        ),
        target_race_date=date(
            2027,
            4,
            26,
        ),
    )

    assert any(
        phase.compressed
        for phase in allocation.phases
    )


def test_minimum_phase_lengths_are_preserved() -> None:
    allocation = allocate_coaching_phases(
        planning_date=date(
            2027,
            3,
            1,
        ),
        target_race_date=date(
            2027,
            4,
            19,
        ),
    )

    lengths = {
        phase.phase: phase.allocated_weeks
        for phase in allocation.phases
    }

    assert lengths[
        TrainingPhase.BASE
    ] >= 2

    assert lengths[
        TrainingPhase.BUILD
    ] >= 2

    assert lengths[
        TrainingPhase.SPECIFIC
    ] >= 2

    assert lengths[
        TrainingPhase.TAPER
    ] >= 1


def test_impossible_horizon_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="insuffisant",
    ):
        allocate_coaching_phases(
            planning_date=date(
                2027,
                3,
                1,
            ),
            target_race_date=date(
                2027,
                3,
                22,
            ),
        )


def test_past_target_race_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="postérieure",
    ):
        allocate_coaching_phases(
            planning_date=date(
                2027,
                3,
                1,
            ),
            target_race_date=date(
                2027,
                2,
                28,
            ),
        )


def test_phase_on_returns_current_phase() -> None:
    allocation = allocate_coaching_phases(
        planning_date=date(
            2027,
            1,
            1,
        ),
        target_race_date=date(
            2027,
            4,
            16,
        ),
    )

    first_phase = allocation.phases[0]

    assert (
        allocation.phase_on(
            first_phase.start_date
        )
        is first_phase.phase
    )

    assert (
        allocation.phase_on(
            first_phase.end_date
        )
        is first_phase.phase
    )


def test_phase_on_returns_none_outside_allocation() -> None:
    allocation = allocate_coaching_phases(
        planning_date=date(
            2027,
            1,
            1,
        ),
        target_race_date=date(
            2027,
            4,
            16,
        ),
    )

    assert (
        allocation.phase_on(
            date(
                2026,
                12,
                1,
            )
        )
        is None
    )


def test_phase_policy_rejects_invalid_duration() -> None:
    with pytest.raises(
        ValueError,
        match="préférée",
    ):
        PhaseDurationPolicy(
            phase=TrainingPhase.BASE,
            minimum_weeks=4,
            preferred_weeks=2,
        )


def test_allocated_phase_requires_positive_duration() -> None:
    with pytest.raises(
        ValueError,
        match="au moins une semaine",
    ):
        AllocatedTrainingPhase(
            phase=TrainingPhase.BASE,
            start_date=date(
                2027,
                1,
                1,
            ),
            end_date=date(
                2027,
                1,
                7,
            ),
            allocated_weeks=0,
            compressed=False,
        )


def test_total_weeks_matches_allocated_phases() -> None:
    allocation = allocate_coaching_phases(
        planning_date=date(
            2027,
            1,
            1,
        ),
        target_race_date=date(
            2027,
            4,
            16,
        ),
    )

    assert (
        allocation.total_weeks
        == sum(
            phase.allocated_weeks
            for phase in allocation.phases
        )
    )


def test_preferred_taper_is_prioritized_when_one_extra_week_exists() -> None:
    """Une semaine disponible au-delà des minimums protège le taper."""

    allocation = allocate_coaching_phases(
        planning_date=date(
            2027,
            1,
            1,
        ),
        target_race_date=date(
            2027,
            2,
            26,
        ),
    )

    lengths = {
        phase.phase: phase.allocated_weeks
        for phase in allocation.phases
    }

    assert allocation.total_weeks == 8

    assert lengths[
        TrainingPhase.TAPER
    ] == 2

    assert lengths[
        TrainingPhase.BASE
    ] == 2

    assert lengths[
        TrainingPhase.BUILD
    ] == 2

    assert lengths[
        TrainingPhase.SPECIFIC
    ] == 2


def test_ten_week_horizon_preserves_two_week_taper() -> None:
    """Une préparation de dix semaines conserve deux semaines de taper."""

    allocation = allocate_coaching_phases(
        planning_date=date(
            2026,
            6,
            15,
        ),
        target_race_date=date(
            2026,
            8,
            24,
        ),
    )

    lengths = {
        phase.phase: phase.allocated_weeks
        for phase in allocation.phases
    }

    assert allocation.total_weeks == 10

    assert lengths[
        TrainingPhase.TAPER
    ] == 2

    assert sum(
        lengths.values()
    ) == 10


def test_minimum_horizon_keeps_single_taper_week() -> None:
    """Le taper peut rester à une semaine si aucun surplus n'existe."""

    allocation = allocate_coaching_phases(
        planning_date=date(
            2027,
            1,
            1,
        ),
        target_race_date=date(
            2027,
            2,
            19,
        ),
    )

    lengths = {
        phase.phase: phase.allocated_weeks
        for phase in allocation.phases
    }

    assert allocation.total_weeks == 7

    assert lengths[
        TrainingPhase.TAPER
    ] == 1


def test_preferred_taper_is_prioritized_when_one_extra_week_exists() -> None:
    """Une semaine disponible au-delà des minimums protège le taper."""

    allocation = allocate_coaching_phases(
        planning_date=date(
            2027,
            1,
            1,
        ),
        target_race_date=date(
            2027,
            2,
            26,
        ),
    )

    lengths = {
        phase.phase: phase.allocated_weeks
        for phase in allocation.phases
    }

    assert allocation.total_weeks == 8

    assert lengths[
        TrainingPhase.TAPER
    ] == 2

    assert lengths[
        TrainingPhase.BASE
    ] == 2

    assert lengths[
        TrainingPhase.BUILD
    ] == 2

    assert lengths[
        TrainingPhase.SPECIFIC
    ] == 2


def test_ten_week_horizon_preserves_two_week_taper() -> None:
    """Une préparation de dix semaines conserve deux semaines de taper."""

    allocation = allocate_coaching_phases(
        planning_date=date(
            2026,
            6,
            15,
        ),
        target_race_date=date(
            2026,
            8,
            24,
        ),
    )

    lengths = {
        phase.phase: phase.allocated_weeks
        for phase in allocation.phases
    }

    assert allocation.total_weeks == 10

    assert lengths[
        TrainingPhase.TAPER
    ] == 2

    assert sum(
        lengths.values()
    ) == 10


def test_minimum_horizon_keeps_single_taper_week() -> None:
    """Le taper peut rester à une semaine si aucun surplus n'existe."""

    allocation = allocate_coaching_phases(
        planning_date=date(
            2027,
            1,
            1,
        ),
        target_race_date=date(
            2027,
            2,
            19,
        ),
    )

    lengths = {
        phase.phase: phase.allocated_weeks
        for phase in allocation.phases
    }

    assert allocation.total_weeks == 7

    assert lengths[
        TrainingPhase.TAPER
    ] == 1
