from datetime import date

import pytest

from opencoach.planning.multi_week_trajectory import (
    TrajectoryWeekType,
)
from opencoach.planning.training_history_metrics import (
    TrainingHistoryMetrics,
    WeeklyTrainingAverages,
)
from opencoach.planning.training_trajectory_service import (
    CurrentWeekCoachingInput,
    build_current_week_coaching,
    build_training_trajectory,
)
from opencoach.planning.weekly_stimulus_slot import (
    Weekday,
)
from opencoach.planning.weekly_training_envelope import (
    TrainingPhase,
)


def create_average(
    *,
    training_load: float,
) -> WeeklyTrainingAverages:
    return WeeklyTrainingAverages(
        weeks=1.0,
        sessions=4.0,
        duration_minutes=300.0,
        distance_km=40.0,
        elevation_gain_m=1000.0,
        training_load=training_load,
    )


def create_metrics(
    *,
    load_7: float = 400.0,
    load_28: float = 400.0,
    load_42: float = 400.0,
    load_84: float = 400.0,
) -> TrainingHistoryMetrics:
    return TrainingHistoryMetrics(
        last_7_days=create_average(
            training_load=load_7,
        ),
        last_28_days=create_average(
            training_load=load_28,
        ),
        last_42_days=create_average(
            training_load=load_42,
        ),
        last_84_days=create_average(
            training_load=load_84,
        ),
        longest_activity=None,
        longest_duration_minutes=None,
        longest_distance_km=None,
        highest_elevation_activity=None,
        highest_elevation_gain_m=None,
    )


def create_current_week_input(
    **overrides,
) -> CurrentWeekCoachingInput:
    data = {
        "trajectory_start_date": date(
            2027,
            1,
            4,
        ),
        "planning_date": date(
            2027,
            3,
            22,
        ),
        "target_race_date": date(
            2027,
            4,
            19,
        ),
        "target_distance_km": 50.0,
        "target_elevation_gain_m": 2500.0,
        "history_metrics": create_metrics(),
        "available_days": (
            Weekday.MONDAY,
            Weekday.WEDNESDAY,
            Weekday.FRIDAY,
            Weekday.SUNDAY,
        ),
    }

    data.update(
        overrides
    )

    return CurrentWeekCoachingInput(
        **data
    )


def test_service_builds_baseline_and_trajectory() -> None:
    result = build_training_trajectory(
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
        history_metrics=create_metrics(),
    )

    assert result.baseline.baseline_load == pytest.approx(
        400.0
    )

    assert result.trajectory.baseline_load == pytest.approx(
        400.0
    )

    assert result.trajectory.week_count > 0


def test_trajectory_uses_calculated_baseline() -> None:
    result = build_training_trajectory(
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
        history_metrics=create_metrics(
            load_7=100.0,
            load_28=400.0,
            load_42=390.0,
            load_84=380.0,
        ),
    )

    assert result.baseline.baseline_load > 300.0

    assert (
        result.trajectory.baseline_load
        == pytest.approx(
            result.baseline.baseline_load
        )
    )

    assert (
        result.trajectory.weeks[0].previous_load
        == pytest.approx(
            result.baseline.baseline_load
        )
    )


def test_short_term_spike_does_not_become_direct_baseline() -> None:
    result = build_training_trajectory(
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
        history_metrics=create_metrics(
            load_7=800.0,
            load_28=400.0,
            load_42=390.0,
            load_84=380.0,
        ),
    )

    assert result.baseline.baseline_load < 800.0

    assert (
        result.trajectory.baseline_load
        == pytest.approx(
            result.baseline.baseline_load
        )
    )


def test_empty_history_builds_zero_baseline() -> None:
    result = build_training_trajectory(
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
        history_metrics=create_metrics(
            load_7=0.0,
            load_28=0.0,
            load_42=0.0,
            load_84=0.0,
        ),
    )

    assert result.baseline.baseline_load == 0.0
    assert result.baseline.confidence == 0.0
    assert result.trajectory.baseline_load == 0.0


def test_service_preserves_target_race_date() -> None:
    race_date = date(
        2027,
        4,
        19,
    )

    result = build_training_trajectory(
        planning_date=date(
            2027,
            1,
            4,
        ),
        target_race_date=race_date,
        history_metrics=create_metrics(),
    )

    assert (
        result.trajectory.target_race_date
        == race_date
    )


def test_current_week_is_selected_automatically() -> None:
    result = build_current_week_coaching(
        input_data=create_current_week_input()
    )

    expected = result.trajectory.week_on(
        date(
            2027,
            3,
            22,
        )
    )

    assert expected is not None
    assert result.trajectory_week is expected


def test_late_planning_date_does_not_restart_at_base() -> None:
    result = build_current_week_coaching(
        input_data=create_current_week_input(
            planning_date=date(
                2027,
                3,
                22,
            ),
        )
    )

    assert (
        result.trajectory_week.phase
        is TrainingPhase.SPECIFIC
    )

    assert (
        result.coaching.planned_phase
        is TrainingPhase.SPECIFIC
    )

    assert (
        result.coaching.effective_phase
        is TrainingPhase.SPECIFIC
    )

    assert (
        result.coaching.envelope.phase
        is TrainingPhase.SPECIFIC
    )


def test_build_phase_is_selected_from_persistent_trajectory() -> None:
    result = build_current_week_coaching(
        input_data=create_current_week_input(
            planning_date=date(
                2027,
                2,
                15,
            ),
        )
    )

    assert (
        result.trajectory_week.phase
        is TrainingPhase.BUILD
    )

    assert (
        result.coaching.planned_phase
        is TrainingPhase.BUILD
    )


def test_current_week_uses_trajectory_load() -> None:
    result = build_current_week_coaching(
        input_data=create_current_week_input()
    )

    assert (
        result.coaching.load_target.target_load
        == pytest.approx(
            result.trajectory_week.target_load
        )
    )

    assert (
        result.coaching.envelope.target_load
        == pytest.approx(
            result.trajectory_week.target_load
        )
    )


def test_planned_recovery_week_is_selected_without_double_reduction() -> None:
    result = build_current_week_coaching(
        input_data=create_current_week_input(
            planning_date=date(
                2027,
                1,
                25,
            ),
        )
    )

    assert (
        result.trajectory_week.week_type
        is TrajectoryWeekType.RECOVERY
    )

    assert result.coaching.recovery.recovery_week is True

    assert (
        result.coaching.envelope.target_load
        == pytest.approx(
            result.trajectory_week.target_load
        )
    )


def test_fatigue_can_adapt_selected_trajectory_week() -> None:
    normal = build_current_week_coaching(
        input_data=create_current_week_input(
            planning_date=date(
                2027,
                2,
                15,
            ),
        )
    )

    fatigued = build_current_week_coaching(
        input_data=create_current_week_input(
            planning_date=date(
                2027,
                2,
                15,
            ),
            fatigue_requires_recovery=True,
        )
    )

    assert (
        fatigued.coaching.envelope.target_load
        < normal.coaching.envelope.target_load
    )


def test_weekly_availability_is_propagated() -> None:
    result = build_current_week_coaching(
        input_data=create_current_week_input(
            available_days=(
                Weekday.THURSDAY,
                Weekday.FRIDAY,
                Weekday.SATURDAY,
                Weekday.SUNDAY,
            ),
            athlete_schedule_constrained=True,
        )
    )

    assert (
        result.coaching.envelope.available_days
        == (
            Weekday.THURSDAY,
            Weekday.FRIDAY,
            Weekday.SATURDAY,
            Weekday.SUNDAY,
        )
    )

    assert (
        result.coaching.envelope.athlete_schedule_constrained
        is True
    )


def test_planning_date_cannot_precede_trajectory_start() -> None:
    with pytest.raises(
        ValueError,
        match="précéder",
    ):
        create_current_week_input(
            trajectory_start_date=date(
                2027,
                1,
                4,
            ),
            planning_date=date(
                2027,
                1,
                3,
            ),
        )


def test_planning_date_must_precede_race() -> None:
    with pytest.raises(
        ValueError,
        match="précéder",
    ):
        create_current_week_input(
            planning_date=date(
                2027,
                4,
                19,
            ),
        )


def test_race_must_follow_trajectory_start() -> None:
    with pytest.raises(
        ValueError,
        match="postérieure",
    ):
        create_current_week_input(
            trajectory_start_date=date(
                2027,
                4,
                19,
            ),
            planning_date=date(
                2027,
                4,
                19,
            ),
            target_race_date=date(
                2027,
                4,
                19,
            ),
        )