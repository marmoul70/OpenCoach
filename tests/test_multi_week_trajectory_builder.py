from datetime import date

import pytest

from opencoach.planning.load_recovery_cycle import (
    RecoveryTrigger,
)
from opencoach.planning.multi_week_trajectory import (
    TrajectoryWeekType,
)
from opencoach.planning.multi_week_trajectory_builder import (
    build_multi_week_trajectory,
)
from opencoach.planning.weekly_training_envelope import (
    TrainingPhase,
)


def build_default_trajectory():
    return build_multi_week_trajectory(
        planning_date=date(
            2027,
            1,
            4,
        ),
        target_race_date=date(
            2027,
            4,
            19,
        ),
        baseline_load=400.0,
    )


def test_builder_creates_multi_week_trajectory() -> None:
    trajectory = build_default_trajectory()

    assert trajectory.week_count > 0

    assert trajectory.baseline_load == pytest.approx(
        400.0
    )

    assert trajectory.target_race_date == date(
        2027,
        4,
        19,
    )


def test_first_week_uses_baseline_as_previous_load() -> None:
    trajectory = build_default_trajectory()

    first_week = trajectory.weeks[0]

    assert first_week.previous_load == pytest.approx(
        400.0
    )

    assert (
        first_week.progression_reference_before
        == pytest.approx(400.0)
    )


def test_load_is_chained_between_weeks() -> None:
    trajectory = build_default_trajectory()

    for previous_week, current_week in zip(
        trajectory.weeks,
        trajectory.weeks[1:],
    ):
        assert (
            current_week.previous_load
            == pytest.approx(
                previous_week.target_load
            )
        )


def test_trajectory_contains_expected_phases() -> None:
    trajectory = build_default_trajectory()

    phases = {
        week.phase
        for week in trajectory.weeks
    }

    assert TrainingPhase.BASE in phases
    assert TrainingPhase.BUILD in phases
    assert TrainingPhase.SPECIFIC in phases
    assert TrainingPhase.TAPER in phases


def test_normal_loading_week_advances_progression_reference() -> None:
    trajectory = build_default_trajectory()

    loading_week = next(
        week
        for week in trajectory.weeks
        if (
            week.week_type
            is TrajectoryWeekType.LOADING
        )
    )

    assert (
        loading_week.progression_reference_after
        > loading_week.progression_reference_before
    )

    assert (
        loading_week.target_load
        == pytest.approx(
            loading_week.progression_reference_after
        )
    )


def test_taper_weeks_are_identified() -> None:
    trajectory = build_default_trajectory()

    taper_weeks = [
        week
        for week in trajectory.weeks
        if week.phase is TrainingPhase.TAPER
    ]

    assert taper_weeks

    assert all(
        week.week_type
        is TrajectoryWeekType.TAPER
        for week in taper_weeks
    )


def test_taper_reduces_progression_reference() -> None:
    trajectory = build_default_trajectory()

    taper_weeks = [
        week
        for week in trajectory.weeks
        if week.phase is TrainingPhase.TAPER
    ]

    assert taper_weeks

    assert all(
        week.progression_reference_after
        < week.progression_reference_before
        for week in taper_weeks
    )


def test_planned_recovery_weeks_are_created() -> None:
    trajectory = build_default_trajectory()

    recovery_weeks = [
        week
        for week in trajectory.weeks
        if (
            week.week_type
            is TrajectoryWeekType.RECOVERY
        )
    ]

    assert recovery_weeks

    assert any(
        week.recovery_trigger
        is RecoveryTrigger.PLANNED
        for week in recovery_weeks
    )


def test_recovery_week_reduces_real_target_load() -> None:
    trajectory = build_default_trajectory()

    recovery_week = next(
        week
        for week in trajectory.weeks
        if (
            week.week_type
            is TrajectoryWeekType.RECOVERY
        )
    )

    assert (
        recovery_week.target_load
        < recovery_week.previous_load
    )


def test_recovery_preserves_progression_reference() -> None:
    trajectory = build_default_trajectory()

    recovery_week = next(
        week
        for week in trajectory.weeks
        if (
            week.week_type
            is TrajectoryWeekType.RECOVERY
        )
    )

    assert (
        recovery_week.progression_reference_after
        == pytest.approx(
            recovery_week.progression_reference_before
        )
    )

    assert (
        recovery_week.target_load
        < recovery_week.progression_reference_before
    )


def test_post_recovery_progression_uses_preserved_reference() -> None:
    trajectory = build_default_trajectory()

    recovery_index = next(
        index
        for index, week in enumerate(
            trajectory.weeks
        )
        if (
            week.week_type
            is TrajectoryWeekType.RECOVERY
        )
    )

    recovery_week = trajectory.weeks[
        recovery_index
    ]

    next_week = trajectory.weeks[
        recovery_index + 1
    ]

    assert (
        next_week.progression_reference_before
        == pytest.approx(
            recovery_week.progression_reference_after
        )
    )

    assert (
        next_week.target_load
        > recovery_week.target_load
    )


def test_post_recovery_progression_advances_from_reference() -> None:
    trajectory = build_default_trajectory()

    recovery_index = next(
        index
        for index, week in enumerate(
            trajectory.weeks
        )
        if (
            week.week_type
            is TrajectoryWeekType.RECOVERY
        )
    )

    next_week = trajectory.weeks[
        recovery_index + 1
    ]

    assert (
        next_week.progression_reference_after
        > next_week.progression_reference_before
    )


def test_progression_can_recover_above_pre_recovery_load() -> None:
    trajectory = build_default_trajectory()

    recovery_index = next(
        index
        for index, week in enumerate(
            trajectory.weeks
        )
        if (
            week.week_type
            is TrajectoryWeekType.RECOVERY
        )
    )

    before_recovery = trajectory.weeks[
        recovery_index - 1
    ]

    weeks_after = trajectory.weeks[
        recovery_index + 1 :
    ]

    assert any(
        week.target_load
        > before_recovery.target_load
        for week in weeks_after
        if week.phase is not TrainingPhase.TAPER
    )


def test_phase_week_index_restarts_at_phase_transition() -> None:
    trajectory = build_default_trajectory()

    previous_phase = None

    for week in trajectory.weeks:
        if week.phase is not previous_phase:
            assert week.phase_week_index == 1

        previous_phase = week.phase


def test_phase_transition_does_not_force_recovery() -> None:
    trajectory = build_default_trajectory()

    for previous_week, current_week in zip(
        trajectory.weeks,
        trajectory.weeks[1:],
    ):
        if current_week.phase is previous_week.phase:
            continue

        if current_week.phase is TrainingPhase.TAPER:
            continue

        assert (
            current_week.recovery_trigger
            is not RecoveryTrigger.PHASE_TRANSITION
        )


def test_taper_does_not_create_recovery_week() -> None:
    trajectory = build_default_trajectory()

    assert all(
        week.week_type
        is not TrajectoryWeekType.RECOVERY
        for week in trajectory.weeks
        if week.phase is TrainingPhase.TAPER
    )


def test_taper_is_cumulative() -> None:
    trajectory = build_default_trajectory()

    taper_weeks = [
        week
        for week in trajectory.weeks
        if week.phase is TrainingPhase.TAPER
    ]

    assert len(taper_weeks) >= 2

    first_taper = taper_weeks[0]
    second_taper = taper_weeks[1]

    assert (
        second_taper.progression_reference_before
        == pytest.approx(
            first_taper.progression_reference_after
        )
    )

    assert (
        second_taper.target_load
        < first_taper.target_load
    )


def test_negative_baseline_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="référence",
    ):
        build_multi_week_trajectory(
            planning_date=date(
                2027,
                1,
                4,
            ),
            target_race_date=date(
                2027,
                4,
                19,
            ),
            baseline_load=-1.0,
        )