from datetime import date

import pytest

from opencoach.planning.history.load_reconciliation import (
    ReconciliationTrendStatus,
)
from opencoach.planning.trajectory.multi_week import (
    TrajectoryWeekType,
)
from opencoach.planning.history.metrics import (
    TrainingHistoryMetrics,
    WeeklyTrainingAverages,
)
from opencoach.planning.trajectory.service import (
    CurrentWeekCoachingInput,
    build_current_week_coaching,
    build_training_trajectory,
)
from opencoach.planning.trajectory.adjustment import (
    LoadAdjustment,
    ProgressionAdjustment,
)
from opencoach.planning.weekly.load_reconciliation import (
    LoadReconciliationStatus,
    reconcile_weekly_load,
)
from opencoach.planning.weekly.load_reconciliation_context import (
    LoadDeviationCause,
    contextualize_weekly_load_reconciliation,
)
from opencoach.planning.weekly.schedule_types import (
    Weekday,
)
from opencoach.planning.weekly.training_envelope import (
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


def create_history_week(
    *,
    planned_load: float,
    actual_load: float,
    cause: LoadDeviationCause,
):
    reconciliation = reconcile_weekly_load(
        planned_load=planned_load,
        actual_load=actual_load,
    )

    return contextualize_weekly_load_reconciliation(
        reconciliation=reconciliation,
        cause=cause,
    )


def test_service_builds_baseline_and_trajectory() -> None:
    result = build_training_trajectory(
        planning_date=date(2027, 1, 4),
        target_race_date=date(2027, 4, 19),
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
        planning_date=date(2027, 1, 4),
        target_race_date=date(2027, 4, 19),
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
        planning_date=date(2027, 1, 4),
        target_race_date=date(2027, 4, 19),
        history_metrics=create_metrics(
            load_7=800.0,
            load_28=400.0,
            load_42=390.0,
            load_84=380.0,
        ),
    )

    assert result.baseline.baseline_load < 800.0


def test_empty_history_builds_zero_baseline() -> None:
    result = build_training_trajectory(
        planning_date=date(2027, 1, 4),
        target_race_date=date(2027, 4, 19),
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
    result = build_training_trajectory(
        planning_date=date(2027, 1, 4),
        target_race_date=date(2027, 4, 19),
        history_metrics=create_metrics(),
    )

    assert (
        result.trajectory.target_race_date
        == date(2027, 4, 19)
    )


def test_current_week_is_selected_automatically() -> None:
    result = build_current_week_coaching(
        input_data=create_current_week_input()
    )

    expected = result.trajectory.week_on(
        date(2027, 3, 22)
    )

    assert expected is not None
    assert result.trajectory_week is expected


def test_late_planning_date_does_not_restart_at_base() -> None:
    result = build_current_week_coaching(
        input_data=create_current_week_input()
    )

    assert (
        result.trajectory_week.phase
        is TrainingPhase.SPECIFIC
    )

    assert (
        result.coaching.planned_phase
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


def test_without_history_trajectory_is_not_reanchored() -> None:
    result = build_current_week_coaching(
        input_data=create_current_week_input()
    )

    assert (
        result.reconciliation_trend.status
        is ReconciliationTrendStatus.STABLE
    )

    assert (
        result.trajectory
        == result.original_trajectory
    )


def test_current_week_uses_trajectory_load_without_reconciliation() -> None:
    result = build_current_week_coaching(
        input_data=create_current_week_input()
    )

    assert result.reconciliation is None

    assert (
        result.coaching.envelope.target_load
        == pytest.approx(
            result.trajectory_week.target_load
        )
    )


def test_previous_week_is_selected_for_reconciliation() -> None:
    result = build_current_week_coaching(
        input_data=create_current_week_input(
            previous_week_actual_load=500.0,
        )
    )

    assert result.previous_trajectory_week is not None

    assert (
        result.previous_trajectory_week.week_start
        == date(2027, 3, 15)
    )

    assert result.reconciliation is not None


def test_on_target_previous_week_keeps_current_target() -> None:
    baseline = build_current_week_coaching(
        input_data=create_current_week_input()
    )

    previous_week = baseline.original_trajectory.week_on(
        date(2027, 3, 15)
    )

    assert previous_week is not None

    result = build_current_week_coaching(
        input_data=create_current_week_input(
            previous_week_actual_load=(
                previous_week.target_load
            ),
        )
    )

    assert (
        result.reconciliation.status
        is LoadReconciliationStatus.ON_TARGET
    )

    assert (
        result.trajectory
        == result.original_trajectory
    )


def test_one_professional_underload_does_not_reanchor() -> None:
    baseline = build_current_week_coaching(
        input_data=create_current_week_input()
    )

    previous_week = baseline.original_trajectory.week_on(
        date(2027, 3, 15)
    )

    assert previous_week is not None

    result = build_current_week_coaching(
        input_data=create_current_week_input(
            previous_week_actual_load=(
                previous_week.target_load * 0.70
            ),
            previous_week_deviation_cause=(
                LoadDeviationCause.PROFESSIONAL_CONSTRAINT
            ),
        )
    )

    assert (
        result.reconciliation_trend.status
        is ReconciliationTrendStatus.STABLE
    )

    assert (
        result.trajectory
        == result.original_trajectory
    )


def test_two_consecutive_underloads_trigger_watch() -> None:
    baseline = build_current_week_coaching(
        input_data=create_current_week_input()
    )

    current = baseline.original_trajectory.week_on(
        date(2027, 3, 22)
    )

    previous = baseline.original_trajectory.week_on(
        date(2027, 3, 15)
    )

    assert current is not None
    assert previous is not None

    older = create_history_week(
        planned_load=500.0,
        actual_load=350.0,
        cause=LoadDeviationCause.PROFESSIONAL_CONSTRAINT,
    )

    result = build_current_week_coaching(
        input_data=create_current_week_input(
            reconciliation_history=(
                older,
            ),
            previous_week_actual_load=(
                previous.target_load * 0.70
            ),
            previous_week_deviation_cause=(
                LoadDeviationCause.PROFESSIONAL_CONSTRAINT
            ),
        )
    )

    assert (
        result.reconciliation_trend.status
        is ReconciliationTrendStatus.WATCH
    )

    assert (
        result.trajectory_week.progression_reference_before
        == pytest.approx(
            current.progression_reference_before
        )
    )


def test_three_consecutive_underloads_reanchor_current_week() -> None:
    baseline = build_current_week_coaching(
        input_data=create_current_week_input()
    )

    original_current = (
        baseline.original_trajectory.week_on(
            date(2027, 3, 22)
        )
    )

    previous = (
        baseline.original_trajectory.week_on(
            date(2027, 3, 15)
        )
    )

    assert original_current is not None
    assert previous is not None

    history = (
        create_history_week(
            planned_load=500.0,
            actual_load=350.0,
            cause=(
                LoadDeviationCause.PROFESSIONAL_CONSTRAINT
            ),
        ),
        create_history_week(
            planned_load=500.0,
            actual_load=350.0,
            cause=(
                LoadDeviationCause.PROFESSIONAL_CONSTRAINT
            ),
        ),
    )

    result = build_current_week_coaching(
        input_data=create_current_week_input(
            reconciliation_history=history,
            previous_week_actual_load=(
                previous.target_load * 0.70
            ),
            previous_week_deviation_cause=(
                LoadDeviationCause.PROFESSIONAL_CONSTRAINT
            ),
        )
    )

    assert (
        result.reconciliation_trend.status
        is ReconciliationTrendStatus.REANCHOR
    )

    assert (
        result.reconciliation_trend.reanchoring_applied
        is True
    )

    assert (
        result.trajectory_week.progression_reference_before
        == pytest.approx(
            result.reconciliation_trend.recommended_reference_load
        )
    )

    assert (
        result.trajectory_week.progression_reference_before
        < original_current.progression_reference_before
    )


def test_reanchor_preserves_original_trajectory_for_audit() -> None:
    baseline = build_current_week_coaching(
        input_data=create_current_week_input()
    )

    previous = baseline.original_trajectory.week_on(
        date(2027, 3, 15)
    )

    assert previous is not None

    history = (
        create_history_week(
            planned_load=500.0,
            actual_load=350.0,
            cause=LoadDeviationCause.PROFESSIONAL_CONSTRAINT,
        ),
        create_history_week(
            planned_load=500.0,
            actual_load=350.0,
            cause=LoadDeviationCause.PROFESSIONAL_CONSTRAINT,
        ),
    )

    result = build_current_week_coaching(
        input_data=create_current_week_input(
            reconciliation_history=history,
            previous_week_actual_load=(
                previous.target_load * 0.70
            ),
            previous_week_deviation_cause=(
                LoadDeviationCause.PROFESSIONAL_CONSTRAINT
            ),
        )
    )

    original_week = (
        result.original_trajectory.week_on(
            date(2027, 3, 22)
        )
    )

    effective_week = (
        result.trajectory.week_on(
            date(2027, 3, 22)
        )
    )

    assert original_week is not None
    assert effective_week is not None

    assert (
        original_week.progression_reference_before
        != pytest.approx(
            effective_week.progression_reference_before
        )
    )


def test_reanchor_does_not_change_historical_baseline() -> None:
    baseline = build_current_week_coaching(
        input_data=create_current_week_input()
    )

    previous = baseline.original_trajectory.week_on(
        date(2027, 3, 15)
    )

    assert previous is not None

    history = (
        create_history_week(
            planned_load=500.0,
            actual_load=350.0,
            cause=LoadDeviationCause.PROFESSIONAL_CONSTRAINT,
        ),
        create_history_week(
            planned_load=500.0,
            actual_load=350.0,
            cause=LoadDeviationCause.PROFESSIONAL_CONSTRAINT,
        ),
    )

    result = build_current_week_coaching(
        input_data=create_current_week_input(
            reconciliation_history=history,
            previous_week_actual_load=(
                previous.target_load * 0.70
            ),
            previous_week_deviation_cause=(
                LoadDeviationCause.PROFESSIONAL_CONSTRAINT
            ),
        )
    )

    assert (
        result.trajectory.baseline_load
        == pytest.approx(
            result.original_trajectory.baseline_load
        )
    )


def test_professional_reanchor_does_not_become_fatigue() -> None:
    baseline = build_current_week_coaching(
        input_data=create_current_week_input()
    )

    previous = baseline.original_trajectory.week_on(
        date(2027, 3, 15)
    )

    assert previous is not None

    history = (
        create_history_week(
            planned_load=500.0,
            actual_load=350.0,
            cause=LoadDeviationCause.PROFESSIONAL_CONSTRAINT,
        ),
        create_history_week(
            planned_load=500.0,
            actual_load=350.0,
            cause=LoadDeviationCause.PROFESSIONAL_CONSTRAINT,
        ),
    )

    result = build_current_week_coaching(
        input_data=create_current_week_input(
            reconciliation_history=history,
            previous_week_actual_load=(
                previous.target_load * 0.70
            ),
            previous_week_deviation_cause=(
                LoadDeviationCause.PROFESSIONAL_CONSTRAINT
            ),
            previous_week_athlete_imposed=True,
        )
    )

    assert (
        result.reconciliation_adjustment.load
        is LoadAdjustment.MAINTAIN
    )

    assert (
        result.reconciliation_trend.status
        is ReconciliationTrendStatus.REANCHOR
    )


def test_fatigue_underload_reduces_current_week() -> None:
    baseline = build_current_week_coaching(
        input_data=create_current_week_input()
    )

    previous_week = baseline.original_trajectory.week_on(
        date(2027, 3, 15)
    )

    assert previous_week is not None

    result = build_current_week_coaching(
        input_data=create_current_week_input(
            previous_week_actual_load=(
                previous_week.target_load * 0.80
            ),
            previous_week_deviation_cause=(
                LoadDeviationCause.FATIGUE
            ),
        )
    )

    assert (
        result.reconciliation_adjustment.load
        is LoadAdjustment.REDUCE_SLIGHTLY
    )

    assert (
        result.coaching.envelope.target_load
        < result.trajectory_week.target_load
    )


def test_strong_overload_protects_current_week() -> None:
    baseline = build_current_week_coaching(
        input_data=create_current_week_input()
    )

    previous_week = baseline.original_trajectory.week_on(
        date(2027, 3, 15)
    )

    assert previous_week is not None

    result = build_current_week_coaching(
        input_data=create_current_week_input(
            previous_week_actual_load=(
                previous_week.target_load * 1.40
            ),
            previous_week_deviation_cause=(
                LoadDeviationCause.UNKNOWN
            ),
        )
    )

    assert (
        result.reconciliation_adjustment.load
        is LoadAdjustment.REDUCE
    )

    assert (
        result.reconciliation_adjustment.progression
        is ProgressionAdjustment.SLOW
    )


def test_reconciliation_and_manual_adjustment_are_consolidated() -> None:
    baseline = build_current_week_coaching(
        input_data=create_current_week_input()
    )

    previous_week = baseline.original_trajectory.week_on(
        date(2027, 3, 15)
    )

    assert previous_week is not None

    result = build_current_week_coaching(
        input_data=create_current_week_input(
            previous_week_actual_load=(
                previous_week.target_load * 0.80
            ),
            previous_week_deviation_cause=(
                LoadDeviationCause.FATIGUE
            ),
            load_adjustment=LoadAdjustment.REDUCE,
        )
    )

    assert (
        result.coaching.resolved_adjustment.load
        is LoadAdjustment.REDUCE
    )


def test_no_previous_week_means_no_reconciliation() -> None:
    result = build_current_week_coaching(
        input_data=create_current_week_input(
            planning_date=date(2027, 1, 4),
            previous_week_actual_load=300.0,
        )
    )

    assert result.previous_trajectory_week is None
    assert result.reconciliation is None
    assert result.reconciliation_context is None
    assert result.reconciliation_adjustment is None


def test_planned_recovery_week_is_selected_without_double_reduction() -> None:
    result = build_current_week_coaching(
        input_data=create_current_week_input(
            planning_date=date(2027, 1, 25),
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
            planning_date=date(2027, 2, 15),
        )
    )

    fatigued = build_current_week_coaching(
        input_data=create_current_week_input(
            planning_date=date(2027, 2, 15),
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

    assert result.coaching.envelope.available_days == (
        Weekday.THURSDAY,
        Weekday.FRIDAY,
        Weekday.SATURDAY,
        Weekday.SUNDAY,
    )

    assert (
        result.coaching.envelope.athlete_schedule_constrained
        is True
    )


def test_negative_previous_actual_load_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="réalisée",
    ):
        create_current_week_input(
            previous_week_actual_load=-1.0,
        )


def test_planning_date_cannot_precede_trajectory_start() -> None:
    with pytest.raises(
        ValueError,
        match="précéder",
    ):
        create_current_week_input(
            trajectory_start_date=date(2027, 1, 4),
            planning_date=date(2027, 1, 3),
        )


def test_planning_date_must_precede_race() -> None:
    with pytest.raises(
        ValueError,
        match="précéder",
    ):
        create_current_week_input(
            planning_date=date(2027, 4, 19),
        )


def test_race_must_follow_trajectory_start() -> None:
    with pytest.raises(
        ValueError,
        match="postérieure",
    ):
        create_current_week_input(
            trajectory_start_date=date(2027, 4, 19),
            planning_date=date(2027, 4, 19),
            target_race_date=date(2027, 4, 19),
        )
def test_current_week_propagates_session_frequency_and_uses_trajectory_duration() -> None:
    input_data = create_current_week_input(
        target_session_count=4,
        reference_weekly_duration_minutes=300.0,
    )

    result = build_current_week_coaching(
        input_data=input_data
    )

    envelope = result.coaching.envelope

    assert envelope.session_count == 4

    assert (
        envelope.reference_duration_minutes
        == 300.0
    )

    assert (
        result.trajectory_week.target_duration_minutes
        is not None
    )

    assert (
        envelope.target_duration_minutes
        == pytest.approx(
            result.trajectory_week.target_duration_minutes
        )
    )

    assert (
        envelope.target_duration_minutes
        != envelope.reference_duration_minutes
    )

def test_training_trajectory_uses_recent_duration_as_volume_baseline() -> None:
    """La trajectoire horaire démarre du volume récent de l'athlète."""

    result = build_training_trajectory(
        planning_date=date(2027, 1, 4),
        target_race_date=date(2027, 4, 19),
        target_distance_km=70.0,
        target_elevation_gain_m=3500.0,
        history_metrics=create_metrics(),
    )

    assert (
        result.trajectory.baseline_duration_minutes
        == pytest.approx(300.0)
    )


def test_training_trajectory_uses_race_volume_demand() -> None:
    """La course cible détermine le pic de volume spécifique."""

    result = build_training_trajectory(
        planning_date=date(2027, 1, 4),
        target_race_date=date(2027, 4, 19),
        target_distance_km=70.0,
        target_elevation_gain_m=3500.0,
        history_metrics=create_metrics(),
    )

    assert (
        result.trajectory.goal_duration_demand_minutes
        == pytest.approx(420.0)
    )

    volume_weeks = tuple(
        week
        for week in result.trajectory.weeks
        if week.target_duration_minutes is not None
    )

    assert volume_weeks

    assert max(
        week.target_duration_minutes
        for week in volume_weeks
        if week.phase is not TrainingPhase.TAPER
    ) >= 400.0
