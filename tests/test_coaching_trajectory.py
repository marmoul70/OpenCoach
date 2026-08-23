from datetime import date

from opencoach.planning.coaching_trajectory import (
    CoachingTrajectoryInput,
    build_coaching_trajectory,
)
from opencoach.planning.trajectory_adjustment import (
    LoadAdjustment,
)
from opencoach.planning.weekly_stimulus_slot import (
    Weekday,
)
from opencoach.planning.weekly_training_envelope import (
    TrainingPhase,
)
from opencoach.planning.trajectory_event import (
    EventImpact,
    TrajectoryEvent,
    TrajectoryEventType,
)
from opencoach.planning.return_to_training_clearance import (
    ReadinessAnswer,
    ReturnToTrainingReadiness,
)
from opencoach.planning.return_to_training_resolver import (
    ReturnToTrainingStatus,
)

def create_input(
    **overrides,
) -> CoachingTrajectoryInput:
    data = {
        "planning_date": date(
            2027,
            3,
            1,
        ),
        "target_race_date": date(
            2027,
            7,
            10,
        ),
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
        "load_adjustment": (
            LoadAdjustment.MAINTAIN
        ),
    }

    data.update(
        overrides
    )

    return CoachingTrajectoryInput(
        **data
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

    assert (
        result.effective_phase
        is result.planned_phase
    )

    assert (
        result.envelope.phase
        is result.effective_phase
    )

    assert result.envelope.session_count > 0


def test_race_profile_is_propagated() -> None:
    result = build_coaching_trajectory(
        input_data=create_input()
    )

    assert (
        result.race_profile.distance_km
        == 50.0
    )

    assert (
        result.race_profile.elevation_gain_m
        == 2500.0
    )


def test_load_is_based_on_previous_week() -> None:
    result = build_coaching_trajectory(
        input_data=create_input(
            previous_load=200.0,
        )
    )

    assert (
        result.load_target.previous_load
        == 200.0
    )


def test_fatigue_can_trigger_recovery() -> None:
    result = build_coaching_trajectory(
        input_data=create_input(
            fatigue_requires_recovery=True,
        )
    )

    assert result.recovery.recovery_week is True

    assert (
        result.envelope.target_load
        < result.load_target.target_load
    )


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

    assert (
        result.envelope.athlete_schedule_constrained
        is True
    )

    assert (
        result.envelope.available_days
        == (
            Weekday.THURSDAY,
            Weekday.FRIDAY,
            Weekday.SATURDAY,
            Weekday.SUNDAY,
        )
    )


def test_load_adjustment_is_applied() -> None:
    maintained = build_coaching_trajectory(
        input_data=create_input(
            load_adjustment=(
                LoadAdjustment.MAINTAIN
            ),
        )
    )

    reduced = build_coaching_trajectory(
        input_data=create_input(
            load_adjustment=(
                LoadAdjustment.REDUCE
            ),
        )
    )

    assert (
        reduced.envelope.target_load
        < maintained.envelope.target_load
    )

def test_active_injury_does_not_start_return_phase() -> None:
    injury = TrajectoryEvent(
        event_id="injury",
        event_type=TrajectoryEventType.INJURY,
        start_date=date(
            2027,
            2,
            25,
        ),
        end_date=date(
            2027,
            3,
            14,
        ),
        impact=EventImpact.HIGH,
    )

    result = build_coaching_trajectory(
        input_data=create_input(
            events=(
                injury,
            ),
        )
    )

    assert (
        result.effective_phase
        is result.planned_phase
    )

    assert result.return_to_training.active is False
    assert result.recovery.recovery_week is True

def test_finished_injury_starts_return_phase() -> None:
    injury = TrajectoryEvent(
        event_id="injury",
        event_type=TrajectoryEventType.INJURY,
        start_date=date(
            2027,
            2,
            1,
        ),
        end_date=date(
            2027,
            2,
            28,
        ),
        impact=EventImpact.HIGH,
    )

    result = build_coaching_trajectory(
        input_data=create_input(
            events=(
                injury,
            ),
        )
    )

    assert (
        result.effective_phase
        is TrainingPhase.RETURN_TO_TRAINING
    )

    assert (
        result.envelope.phase
        is TrainingPhase.RETURN_TO_TRAINING
    )

    assert result.return_to_training.active is True

    assert result.return_to_training.state is not None

    assert (
        result.return_to_training.state.week_index
        == 1
    )

def test_normal_week_keeps_planned_phase_as_effective_phase() -> None:
    result = build_coaching_trajectory(
        input_data=create_input()
    )

    assert (
        result.effective_phase
        is result.planned_phase
    )

def test_missing_readiness_keeps_return_phase_after_minimum() -> None:
    injury = TrajectoryEvent(
        event_id="injury",
        event_type=TrajectoryEventType.INJURY,
        start_date=date(
            2027,
            1,
            20,
        ),
        end_date=date(
            2027,
            2,
            7,
        ),
        impact=EventImpact.HIGH,
    )

    result = build_coaching_trajectory(
        input_data=create_input(
            events=(
                injury,
            ),
        )
    )

    assert (
        result.return_to_training.status
        is ReturnToTrainingStatus.AWAITING_CLEARANCE
    )

    assert (
        result.effective_phase
        is TrainingPhase.RETURN_TO_TRAINING
    )


def test_ready_athlete_can_leave_return_phase() -> None:
    injury = TrajectoryEvent(
        event_id="injury",
        event_type=TrajectoryEventType.INJURY,
        start_date=date(
            2027,
            1,
            20,
        ),
        end_date=date(
            2027,
            2,
            7,
        ),
        impact=EventImpact.HIGH,
    )

    result = build_coaching_trajectory(
        input_data=create_input(
            events=(
                injury,
            ),
            return_to_training_readiness=(
                ReturnToTrainingReadiness(
                    blocking_symptoms=ReadinessAnswer.NO,
                    recovery_sufficient=ReadinessAnswer.YES,
                    clearance_confirmed=ReadinessAnswer.YES,
                )
            ),
        )
    )

    assert (
        result.return_to_training.status
        is ReturnToTrainingStatus.CLEARED
    )

    assert (
        result.effective_phase
        is result.planned_phase
    )


def test_persistent_symptoms_keep_return_phase_active() -> None:
    injury = TrajectoryEvent(
        event_id="injury",
        event_type=TrajectoryEventType.INJURY,
        start_date=date(
            2027,
            1,
            20,
        ),
        end_date=date(
            2027,
            2,
            7,
        ),
        impact=EventImpact.HIGH,
    )

    result = build_coaching_trajectory(
        input_data=create_input(
            events=(
                injury,
            ),
            return_to_training_readiness=(
                ReturnToTrainingReadiness(
                    blocking_symptoms=ReadinessAnswer.YES,
                    recovery_sufficient=ReadinessAnswer.YES,
                    clearance_confirmed=ReadinessAnswer.YES,
                )
            ),
        )
    )

    assert (
        result.return_to_training.status
        is ReturnToTrainingStatus.AWAITING_CLEARANCE
    )

    assert (
        result.effective_phase
        is TrainingPhase.RETURN_TO_TRAINING
    )