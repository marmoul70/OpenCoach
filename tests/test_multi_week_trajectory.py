from datetime import date

import pytest

from opencoach.planning.load_recovery_cycle import (
    RecoveryTrigger,
)
from opencoach.planning.multi_week_trajectory import (
    MultiWeekTrajectory,
    TrajectoryWeek,
    TrajectoryWeekType,
)
from opencoach.planning.trajectory_adjustment import (
    LoadAdjustment,
)
from opencoach.planning.weekly_training_envelope import (
    TrainingPhase,
)


def create_week(
    *,
    week_start: date = date(2027, 3, 1),
    week_end: date = date(2027, 3, 7),
    phase: TrainingPhase = TrainingPhase.BUILD,
    week_type: TrajectoryWeekType = TrajectoryWeekType.LOADING,
    previous_load: float = 400.0,
    progression_reference_before: float = 400.0,
    progression_reference_after: float = 420.0,
    target_load: float = 420.0,
    load_min: float = 400.0,
    load_max: float = 440.0,
    phase_week_index: int = 1,
) -> TrajectoryWeek:
    return TrajectoryWeek(
        week_start=week_start,
        week_end=week_end,
        phase=phase,
        week_type=week_type,
        previous_load=previous_load,
        progression_reference_before=(
            progression_reference_before
        ),
        progression_reference_after=(
            progression_reference_after
        ),
        target_load=target_load,
        load_min=load_min,
        load_max=load_max,
        load_adjustment=LoadAdjustment.MAINTAIN,
        recovery_trigger=RecoveryTrigger.NONE,
        phase_week_index=phase_week_index,
    )


def test_trajectory_week_accepts_valid_values() -> None:
    week = create_week()

    assert week.phase is TrainingPhase.BUILD

    assert (
        week.week_type
        is TrajectoryWeekType.LOADING
    )

    assert week.target_load == pytest.approx(
        420.0
    )


def test_week_tracks_progression_references() -> None:
    week = create_week(
        previous_load=374.4,
        progression_reference_before=449.9,
        progression_reference_after=467.9,
        target_load=467.9,
        load_min=440.0,
        load_max=490.0,
    )

    assert week.previous_load == pytest.approx(
        374.4
    )

    assert (
        week.progression_reference_before
        == pytest.approx(449.9)
    )

    assert (
        week.progression_reference_after
        == pytest.approx(467.9)
    )

    assert week.target_load == pytest.approx(
        467.9
    )


def test_trajectory_week_rejects_invalid_dates() -> None:
    with pytest.raises(
        ValueError,
        match="fin de semaine",
    ):
        create_week(
            week_start=date(
                2027,
                3,
                8,
            ),
            week_end=date(
                2027,
                3,
                7,
            ),
        )


def test_trajectory_week_rejects_negative_previous_load() -> None:
    with pytest.raises(
        ValueError,
        match="charge",
    ):
        create_week(
            previous_load=-1.0,
        )


def test_trajectory_week_rejects_negative_reference_before() -> None:
    with pytest.raises(
        ValueError,
        match="charge",
    ):
        create_week(
            progression_reference_before=-1.0,
        )


def test_trajectory_week_rejects_negative_reference_after() -> None:
    with pytest.raises(
        ValueError,
        match="charge",
    ):
        create_week(
            progression_reference_after=-1.0,
        )


def test_trajectory_week_rejects_negative_target_load() -> None:
    with pytest.raises(
        ValueError,
        match="charge",
    ):
        create_week(
            target_load=-1.0,
        )


def test_trajectory_week_rejects_target_outside_range() -> None:
    with pytest.raises(
        ValueError,
        match="plage",
    ):
        create_week(
            target_load=500.0,
            load_min=400.0,
            load_max=450.0,
        )


def test_trajectory_week_rejects_invalid_load_range() -> None:
    with pytest.raises(
        ValueError,
        match="minimale",
    ):
        create_week(
            target_load=420.0,
            load_min=450.0,
            load_max=400.0,
        )


def test_phase_week_index_must_be_positive() -> None:
    with pytest.raises(
        ValueError,
        match="index",
    ):
        create_week(
            phase_week_index=0,
        )


def test_multi_week_trajectory_exposes_week_count() -> None:
    trajectory = MultiWeekTrajectory(
        planning_date=date(
            2027,
            3,
            1,
        ),
        target_race_date=date(
            2027,
            3,
            21,
        ),
        baseline_load=400.0,
        weeks=(
            create_week(),
            create_week(
                week_start=date(
                    2027,
                    3,
                    8,
                ),
                week_end=date(
                    2027,
                    3,
                    14,
                ),
                previous_load=420.0,
                progression_reference_before=420.0,
                progression_reference_after=440.0,
                target_load=440.0,
                load_min=420.0,
                load_max=460.0,
                phase_week_index=2,
            ),
        ),
    )

    assert trajectory.week_count == 2


def test_week_on_returns_matching_week() -> None:
    expected = create_week()

    trajectory = MultiWeekTrajectory(
        planning_date=date(
            2027,
            3,
            1,
        ),
        target_race_date=date(
            2027,
            3,
            21,
        ),
        baseline_load=400.0,
        weeks=(
            expected,
        ),
    )

    result = trajectory.week_on(
        date(
            2027,
            3,
            4,
        )
    )

    assert result is expected


def test_week_on_returns_none_outside_trajectory() -> None:
    trajectory = MultiWeekTrajectory(
        planning_date=date(
            2027,
            3,
            1,
        ),
        target_race_date=date(
            2027,
            3,
            21,
        ),
        baseline_load=400.0,
        weeks=(
            create_week(),
        ),
    )

    assert (
        trajectory.week_on(
            date(
                2027,
                4,
                1,
            )
        )
        is None
    )


def test_trajectory_rejects_negative_baseline() -> None:
    with pytest.raises(
        ValueError,
        match="référence",
    ):
        MultiWeekTrajectory(
            planning_date=date(
                2027,
                3,
                1,
            ),
            target_race_date=date(
                2027,
                3,
                21,
            ),
            baseline_load=-1.0,
            weeks=(),
        )


def test_target_race_cannot_precede_planning_date() -> None:
    with pytest.raises(
        ValueError,
        match="course cible",
    ):
        MultiWeekTrajectory(
            planning_date=date(
                2027,
                3,
                10,
            ),
            target_race_date=date(
                2027,
                3,
                1,
            ),
            baseline_load=400.0,
            weeks=(),
        )


def test_trajectory_requires_chronological_weeks() -> None:
    with pytest.raises(
        ValueError,
        match="chronologiquement",
    ):
        MultiWeekTrajectory(
            planning_date=date(
                2027,
                3,
                1,
            ),
            target_race_date=date(
                2027,
                3,
                21,
            ),
            baseline_load=400.0,
            weeks=(
                create_week(
                    week_start=date(
                        2027,
                        3,
                        8,
                    ),
                    week_end=date(
                        2027,
                        3,
                        14,
                    ),
                ),
                create_week(
                    week_start=date(
                        2027,
                        3,
                        1,
                    ),
                    week_end=date(
                        2027,
                        3,
                        7,
                    ),
                ),
            ),
        )