from datetime import date

from opencoach.planning.return_to_training.clearance import (
    ReadinessAnswer,
    ReturnToTrainingReadiness,
)
from opencoach.planning.return_to_training.resolver import (
    ReturnToTrainingStatus,
    resolve_return_to_training,
)
from opencoach.planning.trajectory.event import (
    EventImpact,
    TrajectoryEvent,
    TrajectoryEventType,
)


def create_injury(
    *,
    start_date: date,
    end_date: date,
    impact: EventImpact = EventImpact.HIGH,
) -> TrajectoryEvent:
    return TrajectoryEvent(
        event_id="injury",
        event_type=TrajectoryEventType.INJURY,
        start_date=start_date,
        end_date=end_date,
        impact=impact,
    )


def create_ready_state() -> ReturnToTrainingReadiness:
    return ReturnToTrainingReadiness(
        blocking_symptoms=ReadinessAnswer.NO,
        recovery_sufficient=ReadinessAnswer.YES,
        clearance_confirmed=ReadinessAnswer.YES,
    )


def test_active_event_does_not_start_return_phase() -> None:
    event = create_injury(
        start_date=date(
            2027,
            3,
            1,
        ),
        end_date=date(
            2027,
            3,
            14,
        ),
    )

    result = resolve_return_to_training(
        planning_date=date(
            2027,
            3,
            10,
        ),
        events=(
            event,
        ),
    )

    assert (
        result.status
        is ReturnToTrainingStatus.NONE
    )

    assert result.active is False
    assert result.source_event is None
    assert result.policy is None
    assert result.state is None
    assert result.clearance is None


def test_return_starts_after_event_has_ended() -> None:
    event = create_injury(
        start_date=date(
            2027,
            3,
            1,
        ),
        end_date=date(
            2027,
            3,
            14,
        ),
    )

    result = resolve_return_to_training(
        planning_date=date(
            2027,
            3,
            15,
        ),
        events=(
            event,
        ),
    )

    assert (
        result.status
        is ReturnToTrainingStatus.MINIMUM_ACTIVE
    )

    assert result.active is True
    assert result.source_event is event

    assert result.state is not None
    assert result.state.week_index == 1


def test_return_remains_active_during_minimum_period() -> None:
    event = create_injury(
        start_date=date(
            2027,
            3,
            1,
        ),
        end_date=date(
            2027,
            3,
            14,
        ),
    )

    result = resolve_return_to_training(
        planning_date=date(
            2027,
            3,
            29,
        ),
        events=(
            event,
        ),
    )

    assert (
        result.status
        is ReturnToTrainingStatus.MINIMUM_ACTIVE
    )

    assert result.active is True

    assert result.state is not None
    assert result.state.week_index == 3


def test_missing_readiness_keeps_return_active_after_minimum() -> None:
    event = create_injury(
        start_date=date(
            2027,
            3,
            1,
        ),
        end_date=date(
            2027,
            3,
            14,
        ),
    )

    result = resolve_return_to_training(
        planning_date=date(
            2027,
            4,
            5,
        ),
        events=(
            event,
        ),
    )

    assert (
        result.status
        is ReturnToTrainingStatus.AWAITING_CLEARANCE
    )

    assert result.active is True

    assert result.clearance is not None
    assert result.clearance.allowed is False


def test_completed_minimum_with_symptoms_awaits_clearance() -> None:
    event = create_injury(
        start_date=date(
            2027,
            3,
            1,
        ),
        end_date=date(
            2027,
            3,
            14,
        ),
    )

    result = resolve_return_to_training(
        planning_date=date(
            2027,
            4,
            5,
        ),
        events=(
            event,
        ),
        readiness=ReturnToTrainingReadiness(
            blocking_symptoms=ReadinessAnswer.YES,
            recovery_sufficient=ReadinessAnswer.YES,
            clearance_confirmed=ReadinessAnswer.YES,
        ),
    )

    assert (
        result.status
        is ReturnToTrainingStatus.AWAITING_CLEARANCE
    )

    assert result.active is True

    assert result.clearance is not None
    assert result.clearance.allowed is False


def test_completed_minimum_with_insufficient_recovery_stays_active() -> None:
    event = create_injury(
        start_date=date(
            2027,
            3,
            1,
        ),
        end_date=date(
            2027,
            3,
            14,
        ),
    )

    result = resolve_return_to_training(
        planning_date=date(
            2027,
            4,
            5,
        ),
        events=(
            event,
        ),
        readiness=ReturnToTrainingReadiness(
            blocking_symptoms=ReadinessAnswer.NO,
            recovery_sufficient=ReadinessAnswer.NO,
            clearance_confirmed=ReadinessAnswer.YES,
        ),
    )

    assert (
        result.status
        is ReturnToTrainingStatus.AWAITING_CLEARANCE
    )

    assert result.active is True


def test_completed_minimum_and_ready_is_cleared() -> None:
    event = create_injury(
        start_date=date(
            2027,
            3,
            1,
        ),
        end_date=date(
            2027,
            3,
            14,
        ),
    )

    result = resolve_return_to_training(
        planning_date=date(
            2027,
            4,
            5,
        ),
        events=(
            event,
        ),
        readiness=create_ready_state(),
    )

    assert (
        result.status
        is ReturnToTrainingStatus.CLEARED
    )

    assert result.active is False

    assert result.clearance is not None
    assert result.clearance.allowed is True


def test_required_clearance_can_extend_return_phase() -> None:
    event = create_injury(
        start_date=date(
            2027,
            3,
            1,
        ),
        end_date=date(
            2027,
            3,
            14,
        ),
        impact=EventImpact.HIGH,
    )

    result = resolve_return_to_training(
        planning_date=date(
            2027,
            4,
            5,
        ),
        events=(
            event,
        ),
        readiness=ReturnToTrainingReadiness(
            blocking_symptoms=ReadinessAnswer.NO,
            recovery_sufficient=ReadinessAnswer.YES,
            clearance_confirmed=ReadinessAnswer.NO,
        ),
    )

    assert (
        result.status
        is ReturnToTrainingStatus.AWAITING_CLEARANCE
    )

    assert result.active is True


def test_most_recent_active_return_is_selected() -> None:
    old_event = create_injury(
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
        impact=EventImpact.LOW,
    )

    recent_event = TrajectoryEvent(
        event_id="recent-break",
        event_type=TrajectoryEventType.TRAINING_BREAK,
        start_date=date(
            2027,
            3,
            1,
        ),
        end_date=date(
            2027,
            3,
            14,
        ),
        impact=EventImpact.MODERATE,
    )

    result = resolve_return_to_training(
        planning_date=date(
            2027,
            3,
            15,
        ),
        events=(
            old_event,
            recent_event,
        ),
    )

    assert (
        result.status
        is ReturnToTrainingStatus.MINIMUM_ACTIVE
    )

    assert result.active is True
    assert result.source_event is recent_event