from datetime import date

import pytest

from opencoach.planning.multi_week_trajectory import (
    TrajectoryWeekType,
)
from opencoach.planning.multi_week_trajectory_builder import (
    build_multi_week_trajectory,
)
from opencoach.planning.multi_week_trajectory_reanchoring import (
    reanchor_multi_week_trajectory,
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


def test_reanchor_preserves_past_weeks() -> None:
    original = build_default_trajectory()

    from_date = date(
        2027,
        3,
        1,
    )

    result = reanchor_multi_week_trajectory(
        trajectory=original,
        from_date=from_date,
        new_reference_load=350.0,
    )

    for original_week, rebuilt_week in zip(
        original.weeks,
        result.weeks,
    ):
        if (
            original_week.week_start
            >= from_date
        ):
            break

        assert rebuilt_week == original_week


def test_reanchor_changes_structural_reference() -> None:
    original = build_default_trajectory()

    result = reanchor_multi_week_trajectory(
        trajectory=original,
        from_date=date(
            2027,
            3,
            1,
        ),
        new_reference_load=350.0,
    )

    current_week = result.week_on(
        date(
            2027,
            3,
            1,
        )
    )

    assert current_week is not None

    assert (
        current_week.progression_reference_before
        == pytest.approx(350.0)
    )


def test_reanchor_preserves_phase_schedule() -> None:
    original = build_default_trajectory()

    result = reanchor_multi_week_trajectory(
        trajectory=original,
        from_date=date(
            2027,
            2,
            15,
        ),
        new_reference_load=350.0,
    )

    assert [
        week.phase
        for week in result.weeks
    ] == [
        week.phase
        for week in original.weeks
    ]


def test_reanchor_preserves_week_dates() -> None:
    original = build_default_trajectory()

    result = reanchor_multi_week_trajectory(
        trajectory=original,
        from_date=date(
            2027,
            2,
            15,
        ),
        new_reference_load=350.0,
    )

    assert [
        (
            week.week_start,
            week.week_end,
        )
        for week in result.weeks
    ] == [
        (
            week.week_start,
            week.week_end,
        )
        for week in original.weeks
    ]


def test_reanchor_preserves_week_types() -> None:
    original = build_default_trajectory()

    result = reanchor_multi_week_trajectory(
        trajectory=original,
        from_date=date(
            2027,
            2,
            15,
        ),
        new_reference_load=350.0,
    )

    assert [
        week.week_type
        for week in result.weeks
    ] == [
        week.week_type
        for week in original.weeks
    ]


def test_reanchor_preserves_recovery_triggers() -> None:
    original = build_default_trajectory()

    result = reanchor_multi_week_trajectory(
        trajectory=original,
        from_date=date(
            2027,
            2,
            15,
        ),
        new_reference_load=350.0,
    )

    assert [
        week.recovery_trigger
        for week in result.weeks
    ] == [
        week.recovery_trigger
        for week in original.weeks
    ]


def test_reconnection_caps_first_loading_week() -> None:
    original = build_default_trajectory()

    result = reanchor_multi_week_trajectory(
        trajectory=original,
        from_date=date(
            2027,
            3,
            22,
        ),
        new_reference_load=459.25,
        previous_load=350.0,
    )

    current_week = result.week_on(
        date(
            2027,
            3,
            22,
        )
    )

    assert current_week is not None

    assert (
        current_week.target_load
        == pytest.approx(385.0)
    )

    assert (
        current_week.progression_reference_before
        == pytest.approx(459.25)
    )

    assert (
        current_week.progression_reference_after
        == pytest.approx(459.25)
    )


def test_reconnection_progresses_from_effective_previous_target() -> None:
    original = build_default_trajectory()

    result = reanchor_multi_week_trajectory(
        trajectory=original,
        from_date=date(
            2027,
            3,
            22,
        ),
        new_reference_load=500.0,
        previous_load=350.0,
    )

    first = result.week_on(
        date(
            2027,
            3,
            22,
        )
    )

    second = result.week_on(
        date(
            2027,
            3,
            29,
        )
    )

    assert first is not None
    assert second is not None

    assert (
        first.target_load
        == pytest.approx(385.0)
    )

    assert (
        second.target_load
        == pytest.approx(423.5)
    )


def test_structural_reference_is_frozen_during_reconnection() -> None:
    original = build_default_trajectory()

    result = reanchor_multi_week_trajectory(
        trajectory=original,
        from_date=date(
            2027,
            3,
            22,
        ),
        new_reference_load=500.0,
        previous_load=350.0,
    )

    first = result.week_on(
        date(
            2027,
            3,
            22,
        )
    )

    second = result.week_on(
        date(
            2027,
            3,
            29,
        )
    )

    assert first is not None
    assert second is not None

    assert (
        first.progression_reference_before
        == pytest.approx(500.0)
    )

    assert (
        first.progression_reference_after
        == pytest.approx(500.0)
    )

    assert (
        second.progression_reference_before
        == pytest.approx(500.0)
    )

    assert (
        second.progression_reference_after
        == pytest.approx(500.0)
    )


def test_reconnection_never_jumps_directly_to_reference() -> None:
    original = build_default_trajectory()

    result = reanchor_multi_week_trajectory(
        trajectory=original,
        from_date=date(
            2027,
            3,
            22,
        ),
        new_reference_load=500.0,
        previous_load=350.0,
    )

    current = result.week_on(
        date(
            2027,
            3,
            22,
        )
    )

    assert current is not None

    increase = (
        current.target_load
        - 350.0
    ) / 350.0

    assert increase == pytest.approx(
        0.10
    )


def test_without_observed_load_reanchor_uses_normal_progression() -> None:
    original = build_default_trajectory()

    result = reanchor_multi_week_trajectory(
        trajectory=original,
        from_date=date(
            2027,
            3,
            22,
        ),
        new_reference_load=500.0,
    )

    current = result.week_on(
        date(
            2027,
            3,
            22,
        )
    )

    assert current is not None

    assert (
        current.target_load
        > current.progression_reference_before
    )

    assert (
        current.progression_reference_after
        == pytest.approx(
            current.target_load
        )
    )


def test_reanchored_recovery_preserves_structural_reference() -> None:
    original = build_default_trajectory()

    recovery_week = next(
        week
        for week in original.weeks
        if (
            week.week_type
            is TrajectoryWeekType.RECOVERY
        )
    )

    result = reanchor_multi_week_trajectory(
        trajectory=original,
        from_date=recovery_week.week_start,
        new_reference_load=400.0,
        previous_load=350.0,
    )

    rebuilt = result.week_on(
        recovery_week.week_start
    )

    assert rebuilt is not None

    assert (
        rebuilt.progression_reference_before
        == pytest.approx(400.0)
    )

    assert (
        rebuilt.progression_reference_after
        == pytest.approx(400.0)
    )


def test_recovery_during_reconnection_does_not_exceed_reconnection_cap() -> None:
    original = build_default_trajectory()

    recovery_week = next(
        week
        for week in original.weeks
        if (
            week.week_type
            is TrajectoryWeekType.RECOVERY
        )
    )

    result = reanchor_multi_week_trajectory(
        trajectory=original,
        from_date=recovery_week.week_start,
        new_reference_load=500.0,
        previous_load=300.0,
    )

    rebuilt = result.week_on(
        recovery_week.week_start
    )

    assert rebuilt is not None

    assert rebuilt.target_load <= 330.0 + 1e-9


def test_week_after_recovery_keeps_reconnection_reference() -> None:
    original = build_default_trajectory()

    recovery_index = next(
        index
        for index, week in enumerate(
            original.weeks
        )
        if (
            week.week_type
            is TrajectoryWeekType.RECOVERY
        )
    )

    recovery_week = original.weeks[
        recovery_index
    ]

    result = reanchor_multi_week_trajectory(
        trajectory=original,
        from_date=recovery_week.week_start,
        new_reference_load=500.0,
        previous_load=300.0,
    )

    rebuilt_recovery = result.weeks[
        recovery_index
    ]

    next_week = result.weeks[
        recovery_index + 1
    ]

    assert (
        rebuilt_recovery.progression_reference_after
        == pytest.approx(500.0)
    )

    assert (
        next_week.progression_reference_before
        == pytest.approx(500.0)
    )


def test_taper_has_priority_over_reconnection() -> None:
    original = build_default_trajectory()

    first_taper = next(
        week
        for week in original.weeks
        if (
            week.phase
            is TrainingPhase.TAPER
        )
    )

    result = reanchor_multi_week_trajectory(
        trajectory=original,
        from_date=first_taper.week_start,
        new_reference_load=500.0,
        previous_load=350.0,
    )

    rebuilt_taper = result.week_on(
        first_taper.week_start
    )

    assert rebuilt_taper is not None

    assert (
        rebuilt_taper.week_type
        is TrajectoryWeekType.TAPER
    )

    assert (
        rebuilt_taper.target_load
        < rebuilt_taper.progression_reference_before
    )

    assert (
        rebuilt_taper.progression_reference_after
        < rebuilt_taper.progression_reference_before
    )


def test_reanchored_suffix_keeps_previous_load_chain() -> None:
    original = build_default_trajectory()

    result = reanchor_multi_week_trajectory(
        trajectory=original,
        from_date=date(
            2027,
            2,
            15,
        ),
        new_reference_load=450.0,
        previous_load=325.0,
    )

    start_index = next(
        index
        for index, week in enumerate(
            result.weeks
        )
        if (
            week.week_start
            == date(
                2027,
                2,
                15,
            )
        )
    )

    assert (
        result.weeks[start_index].previous_load
        == pytest.approx(325.0)
    )

    for previous_week, current_week in zip(
        result.weeks[start_index:],
        result.weeks[start_index + 1 :],
    ):
        assert (
            current_week.previous_load
            == pytest.approx(
                previous_week.target_load
            )
        )


def test_reanchor_keeps_original_baseline_for_audit() -> None:
    original = build_default_trajectory()

    result = reanchor_multi_week_trajectory(
        trajectory=original,
        from_date=date(
            2027,
            3,
            22,
        ),
        new_reference_load=459.25,
        previous_load=350.0,
    )

    assert (
        result.baseline_load
        == pytest.approx(
            original.baseline_load
        )
    )


def test_missing_reanchor_week_is_rejected() -> None:
    original = build_default_trajectory()

    with pytest.raises(
        ValueError,
        match="réancrage",
    ):
        reanchor_multi_week_trajectory(
            trajectory=original,
            from_date=date(
                2028,
                1,
                1,
            ),
            new_reference_load=350.0,
        )


def test_negative_reference_is_rejected() -> None:
    original = build_default_trajectory()

    with pytest.raises(
        ValueError,
        match="référence",
    ):
        reanchor_multi_week_trajectory(
            trajectory=original,
            from_date=date(
                2027,
                3,
                22,
            ),
            new_reference_load=-1.0,
        )


def test_negative_previous_load_is_rejected() -> None:
    original = build_default_trajectory()

    with pytest.raises(
        ValueError,
        match="précédente",
    ):
        reanchor_multi_week_trajectory(
            trajectory=original,
            from_date=date(
                2027,
                3,
                22,
            ),
            new_reference_load=350.0,
            previous_load=-1.0,
        )