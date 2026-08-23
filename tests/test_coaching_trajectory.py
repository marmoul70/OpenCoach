from datetime import date

import pytest

from opencoach.planning.coaching_trajectory import (
    CoachingTrajectoryInput,
    build_coaching_trajectory,
)
from opencoach.planning.load_recovery_cycle import (
    RecoveryTrigger,
)
from opencoach.planning.multi_week_trajectory import (
    TrajectoryWeek,
    TrajectoryWeekType,
)
from opencoach.planning.return_to_training_clearance import (
    ReadinessAnswer,
    ReturnToTrainingReadiness,
)
from opencoach.planning.return_to_training_resolver import (
    ReturnToTrainingStatus,
)
from opencoach.planning.trajectory_adjustment import (
    AdjustmentSeverity,
    LoadAdjustment,
    ProgressionAdjustment,
    TrajectoryAdjustment,
)
from opencoach.planning.trajectory_event import (
    EventImpact,
    TrajectoryEvent,
    TrajectoryEventType,
)
from opencoach.planning.weekly_schedule_types import (
    Weekday,
)
from opencoach.planning.weekly_training_envelope import (
    TrainingPhase,
)


def create_input(
    **overrides,
) -> CoachingTrajectoryInput:
    data = {
        "planning_date": date(2027, 3, 1),
        "target_race_date": date(2027, 7, 10),
        "target_distance_km": 50.0,
        "target_elevation_gain_m": 2500.0,
        "previous_load": 100.0,
        "loading_weeks_since_recovery": 1,
        "available_days": (
            Weekday.TUESDAY,
            Weekday.THURSDAY,
            Weekday.SATURDAY,
            Weekday.SUNDAY,
        ),
        "load_adjustment": LoadAdjustment.MAINTAIN,
    }

    data.update(overrides)

    return CoachingTrajectoryInput(**data)


def create_planned_week(
    *,
    phase: TrainingPhase = TrainingPhase.BASE,
    week_type: TrajectoryWeekType = TrajectoryWeekType.LOADING,
    target_load: float = 104.0,
    load_min: float = 98.8,
    load_max: float = 109.2,
    recovery_trigger: RecoveryTrigger = RecoveryTrigger.NONE,
) -> TrajectoryWeek:
    progression_rate = {
        TrainingPhase.BASE: 0.04,
        TrainingPhase.BUILD: 0.06,
        TrainingPhase.SPECIFIC: 0.02,
        TrainingPhase.TAPER: -0.30,
    }.get(
        phase,
        0.0,
    )

    progression_after = (
        100.0
        if week_type is TrajectoryWeekType.RECOVERY
        else 100.0 * (1.0 + progression_rate)
    )

    return TrajectoryWeek(
        week_start=date(2027, 3, 1),
        week_end=date(2027, 3, 7),
        phase=phase,
        week_type=week_type,
        previous_load=100.0,
        progression_reference_before=100.0,
        progression_reference_after=progression_after,
        target_load=target_load,
        load_min=load_min,
        load_max=load_max,
        load_adjustment=LoadAdjustment.MAINTAIN,
        recovery_trigger=recovery_trigger,
        phase_week_index=1,
    )


def create_additional_adjustment(
    *,
    load: LoadAdjustment,
    progression: ProgressionAdjustment = (
        ProgressionAdjustment.CONTINUE
    ),
    requires_return_to_training: bool = False,
) -> TrajectoryAdjustment:
    return TrajectoryAdjustment(
        reason="Adaptation de test.",
        severity=AdjustmentSeverity.MODERATE,
        load=load,
        progression=progression,
        requires_return_to_training=(
            requires_return_to_training
        ),
        athlete_override_allowed=True,
    )


def test_builds_complete_trajectory() -> None:
    result = build_coaching_trajectory(
        input_data=create_input()
    )

    assert result.planned_phase in {
        TrainingPhase.BASE,
        TrainingPhase.BUILD,
        TrainingPhase.SPECIFIC,
        TrainingPhase.TAPER,
    }

    assert result.effective_phase is result.planned_phase
    assert result.envelope.phase is result.effective_phase
    assert result.envelope.session_count > 0


def test_legacy_mode_still_exposes_phase_allocation() -> None:
    result = build_coaching_trajectory(
        input_data=create_input()
    )

    assert result.phase_allocation is not None


def test_trajectory_week_is_source_of_planned_phase() -> None:
    planned_week = create_planned_week(
        phase=TrainingPhase.SPECIFIC,
        target_load=102.0,
        load_min=96.9,
        load_max=107.1,
    )

    result = build_coaching_trajectory(
        input_data=create_input(
            trajectory_week=planned_week,
        )
    )

    assert result.phase_allocation is None
    assert result.planned_phase is TrainingPhase.SPECIFIC
    assert result.effective_phase is TrainingPhase.SPECIFIC
    assert result.envelope.phase is TrainingPhase.SPECIFIC


def test_build_week_can_come_from_non_base_phase() -> None:
    planned_week = create_planned_week(
        phase=TrainingPhase.BUILD,
        target_load=106.0,
        load_min=100.7,
        load_max=111.3,
    )

    result = build_coaching_trajectory(
        input_data=create_input(
            trajectory_week=planned_week,
        )
    )

    assert result.planned_phase is TrainingPhase.BUILD
    assert result.load_target.phase is TrainingPhase.BUILD
    assert result.envelope.phase is TrainingPhase.BUILD


def test_race_profile_is_propagated() -> None:
    result = build_coaching_trajectory(
        input_data=create_input()
    )

    assert result.race_profile.distance_km == 50.0
    assert result.race_profile.elevation_gain_m == 2500.0


def test_legacy_load_is_based_on_previous_week() -> None:
    result = build_coaching_trajectory(
        input_data=create_input(
            previous_load=200.0,
        )
    )

    assert result.load_target.previous_load == 200.0


def test_trajectory_week_supplies_planned_load() -> None:
    planned_week = create_planned_week()

    result = build_coaching_trajectory(
        input_data=create_input(
            previous_load=999.0,
            trajectory_week=planned_week,
        )
    )

    assert result.load_target.previous_load == pytest.approx(100.0)
    assert result.load_target.target_load == pytest.approx(104.0)
    assert result.envelope.target_load == pytest.approx(104.0)
    assert result.trajectory_week is planned_week


def test_planned_recovery_is_not_applied_twice() -> None:
    planned_week = create_planned_week(
        week_type=TrajectoryWeekType.RECOVERY,
        target_load=80.0,
        load_min=76.0,
        load_max=84.0,
        recovery_trigger=RecoveryTrigger.PLANNED,
    )

    result = build_coaching_trajectory(
        input_data=create_input(
            trajectory_week=planned_week,
        )
    )

    assert result.recovery.recovery_week is True
    assert result.recovery.trigger is RecoveryTrigger.PLANNED
    assert result.recovery.load_factor == pytest.approx(1.0)
    assert result.load_target.target_load == pytest.approx(80.0)
    assert result.envelope.target_load == pytest.approx(80.0)


def test_manual_adjustment_can_reduce_planned_week() -> None:
    planned_week = create_planned_week()

    result = build_coaching_trajectory(
        input_data=create_input(
            trajectory_week=planned_week,
            load_adjustment=LoadAdjustment.REDUCE,
        )
    )

    assert result.resolved_adjustment.load is LoadAdjustment.REDUCE

    assert result.load_target.target_load == pytest.approx(
        104.0 * 0.75
    )


def test_additional_adjustment_can_reduce_planned_week() -> None:
    planned_week = create_planned_week()

    adjustment = create_additional_adjustment(
        load=LoadAdjustment.REDUCE_SLIGHTLY,
    )

    result = build_coaching_trajectory(
        input_data=create_input(
            trajectory_week=planned_week,
            additional_adjustments=(adjustment,),
        )
    )

    assert (
        result.resolved_adjustment.load
        is LoadAdjustment.REDUCE_SLIGHTLY
    )

    assert result.load_target.target_load == pytest.approx(
        104.0 * 0.90
    )


def test_event_and_additional_adjustment_are_consolidated() -> None:
    planned_week = create_planned_week()

    adjustment = create_additional_adjustment(
        load=LoadAdjustment.REDUCE,
    )

    event = TrajectoryEvent(
        event_id="injury",
        event_type=TrajectoryEventType.INJURY,
        start_date=date(2027, 2, 25),
        end_date=date(2027, 3, 14),
        impact=EventImpact.HIGH,
    )

    result = build_coaching_trajectory(
        input_data=create_input(
            trajectory_week=planned_week,
            events=(event,),
            additional_adjustments=(adjustment,),
        )
    )

    assert (
        result.resolved_adjustment.load
        is LoadAdjustment.SUSPEND
    )


def test_manual_maintain_cannot_cancel_additional_reduce() -> None:
    adjustment = create_additional_adjustment(
        load=LoadAdjustment.REDUCE,
    )

    result = build_coaching_trajectory(
        input_data=create_input(
            additional_adjustments=(adjustment,),
            load_adjustment=LoadAdjustment.MAINTAIN,
        )
    )

    assert result.resolved_adjustment.load is LoadAdjustment.REDUCE


def test_fatigue_can_reduce_planned_week() -> None:
    planned_week = create_planned_week()

    result = build_coaching_trajectory(
        input_data=create_input(
            trajectory_week=planned_week,
            fatigue_requires_recovery=True,
        )
    )

    assert result.recovery.recovery_week is True
    assert result.recovery.trigger is RecoveryTrigger.FATIGUE
    assert result.envelope.target_load < result.load_target.target_load


def test_trajectory_week_must_cover_planning_date() -> None:
    planned_week = TrajectoryWeek(
        week_start=date(2027, 3, 8),
        week_end=date(2027, 3, 14),
        phase=TrainingPhase.BASE,
        week_type=TrajectoryWeekType.LOADING,
        previous_load=100.0,
        progression_reference_before=100.0,
        progression_reference_after=104.0,
        target_load=104.0,
        load_min=98.8,
        load_max=109.2,
        load_adjustment=LoadAdjustment.MAINTAIN,
        phase_week_index=1,
    )

    with pytest.raises(
        ValueError,
        match="ne couvre pas",
    ):
        build_coaching_trajectory(
            input_data=create_input(
                trajectory_week=planned_week,
            )
        )


def test_fatigue_can_trigger_recovery_without_trajectory() -> None:
    result = build_coaching_trajectory(
        input_data=create_input(
            fatigue_requires_recovery=True,
        )
    )

    assert result.recovery.recovery_week is True
    assert result.envelope.target_load < result.load_target.target_load


def test_schedule_constraint_is_preserved() -> None:
    result = build_coaching_trajectory(
        input_data=create_input(
            available_days=(
                Weekday.THURSDAY,
                Weekday.FRIDAY,
                Weekday.SATURDAY,
                Weekday.SUNDAY,
            ),
            athlete_schedule_constrained=True,
        )
    )

    assert result.envelope.athlete_schedule_constrained is True

    assert result.envelope.available_days == (
        Weekday.THURSDAY,
        Weekday.FRIDAY,
        Weekday.SATURDAY,
        Weekday.SUNDAY,
    )


def test_load_adjustment_is_applied_without_trajectory() -> None:
    maintained = build_coaching_trajectory(
        input_data=create_input()
    )

    reduced = build_coaching_trajectory(
        input_data=create_input(
            load_adjustment=LoadAdjustment.REDUCE,
        )
    )

    assert reduced.envelope.target_load < maintained.envelope.target_load


def test_additional_adjustment_can_require_return_phase() -> None:
    adjustment = create_additional_adjustment(
        load=LoadAdjustment.SUSPEND,
        progression=ProgressionAdjustment.REBUILD,
        requires_return_to_training=True,
    )

    result = build_coaching_trajectory(
        input_data=create_input(
            additional_adjustments=(adjustment,),
        )
    )

    assert (
        result.resolved_adjustment.requires_return_to_training
        is True
    )

    assert (
        result.effective_phase
        is TrainingPhase.RETURN_TO_TRAINING
    )


def test_active_injury_does_not_start_return_phase() -> None:
    injury = TrajectoryEvent(
        event_id="injury",
        event_type=TrajectoryEventType.INJURY,
        start_date=date(2027, 2, 25),
        end_date=date(2027, 3, 14),
        impact=EventImpact.HIGH,
    )

    result = build_coaching_trajectory(
        input_data=create_input(
            events=(injury,),
        )
    )

    assert result.effective_phase is result.planned_phase
    assert result.return_to_training.active is False
    assert result.recovery.recovery_week is True


def test_finished_injury_starts_return_phase() -> None:
    injury = TrajectoryEvent(
        event_id="injury",
        event_type=TrajectoryEventType.INJURY,
        start_date=date(2027, 2, 1),
        end_date=date(2027, 2, 28),
        impact=EventImpact.HIGH,
    )

    result = build_coaching_trajectory(
        input_data=create_input(
            events=(injury,),
        )
    )

    assert result.effective_phase is TrainingPhase.RETURN_TO_TRAINING
    assert result.envelope.phase is TrainingPhase.RETURN_TO_TRAINING
    assert result.return_to_training.active is True
    assert result.return_to_training.state is not None
    assert result.return_to_training.state.week_index == 1


def test_return_to_training_overrides_trajectory_phase() -> None:
    injury = TrajectoryEvent(
        event_id="injury",
        event_type=TrajectoryEventType.INJURY,
        start_date=date(2027, 2, 1),
        end_date=date(2027, 2, 28),
        impact=EventImpact.HIGH,
    )

    planned_week = create_planned_week(
        phase=TrainingPhase.SPECIFIC,
        target_load=102.0,
        load_min=96.9,
        load_max=107.1,
    )

    result = build_coaching_trajectory(
        input_data=create_input(
            trajectory_week=planned_week,
            events=(injury,),
        )
    )

    assert result.planned_phase is TrainingPhase.SPECIFIC
    assert result.effective_phase is TrainingPhase.RETURN_TO_TRAINING
    assert result.load_target.phase is TrainingPhase.RETURN_TO_TRAINING


def test_normal_week_keeps_planned_phase_as_effective_phase() -> None:
    result = build_coaching_trajectory(
        input_data=create_input()
    )

    assert result.effective_phase is result.planned_phase


def test_missing_readiness_keeps_return_phase_after_minimum() -> None:
    injury = TrajectoryEvent(
        event_id="injury",
        event_type=TrajectoryEventType.INJURY,
        start_date=date(2027, 1, 20),
        end_date=date(2027, 2, 7),
        impact=EventImpact.HIGH,
    )

    result = build_coaching_trajectory(
        input_data=create_input(
            events=(injury,),
        )
    )

    assert (
        result.return_to_training.status
        is ReturnToTrainingStatus.AWAITING_CLEARANCE
    )

    assert result.effective_phase is TrainingPhase.RETURN_TO_TRAINING


def test_ready_athlete_can_leave_return_phase() -> None:
    injury = TrajectoryEvent(
        event_id="injury",
        event_type=TrajectoryEventType.INJURY,
        start_date=date(2027, 1, 20),
        end_date=date(2027, 2, 7),
        impact=EventImpact.HIGH,
    )

    result = build_coaching_trajectory(
        input_data=create_input(
            events=(injury,),
            return_to_training_readiness=ReturnToTrainingReadiness(
                blocking_symptoms=ReadinessAnswer.NO,
                recovery_sufficient=ReadinessAnswer.YES,
                clearance_confirmed=ReadinessAnswer.YES,
            ),
        )
    )

    assert (
        result.return_to_training.status
        is ReturnToTrainingStatus.CLEARED
    )

    assert result.effective_phase is result.planned_phase


def test_persistent_symptoms_keep_return_phase_active() -> None:
    injury = TrajectoryEvent(
        event_id="injury",
        event_type=TrajectoryEventType.INJURY,
        start_date=date(2027, 1, 20),
        end_date=date(2027, 2, 7),
        impact=EventImpact.HIGH,
    )

    result = build_coaching_trajectory(
        input_data=create_input(
            events=(injury,),
            return_to_training_readiness=ReturnToTrainingReadiness(
                blocking_symptoms=ReadinessAnswer.YES,
                recovery_sufficient=ReadinessAnswer.YES,
                clearance_confirmed=ReadinessAnswer.YES,
            ),
        )
    )

    assert (
        result.return_to_training.status
        is ReturnToTrainingStatus.AWAITING_CLEARANCE
    )

    assert result.effective_phase is TrainingPhase.RETURN_TO_TRAINING