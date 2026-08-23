from datetime import date

from opencoach.planning.return_to_training_policy import (
    build_return_to_training_policy,
)
from opencoach.planning.trajectory_event import (
    EventImpact,
    TrajectoryEvent,
    TrajectoryEventType,
)


def create_event(
    *,
    event_type: TrajectoryEventType,
    impact: EventImpact,
    start_day: int = 1,
    end_day: int = 7,
) -> TrajectoryEvent:
    return TrajectoryEvent(
        event_id="event",
        event_type=event_type,
        start_date=date(
            2027,
            3,
            start_day,
        ),
        end_date=date(
            2027,
            3,
            end_day,
        ),
        impact=impact,
    )


def test_low_impact_injury_has_minimum_recovery_period() -> None:
    policy = build_return_to_training_policy(
        create_event(
            event_type=TrajectoryEventType.INJURY,
            impact=EventImpact.LOW,
        )
    )

    assert policy is not None
    assert policy.minimum_weeks == 1
    assert policy.requires_clearance is False


def test_high_impact_injury_requires_longer_return() -> None:
    policy = build_return_to_training_policy(
        create_event(
            event_type=TrajectoryEventType.INJURY,
            impact=EventImpact.HIGH,
        )
    )

    assert policy is not None
    assert policy.minimum_weeks == 3
    assert policy.requires_clearance is True


def test_long_injury_extends_minimum_return() -> None:
    policy = build_return_to_training_policy(
        create_event(
            event_type=TrajectoryEventType.INJURY,
            impact=EventImpact.HIGH,
            start_day=1,
            end_day=31,
        )
    )

    assert policy is not None
    assert policy.minimum_weeks == 4


def test_low_impact_illness_does_not_force_return_phase() -> None:
    policy = build_return_to_training_policy(
        create_event(
            event_type=TrajectoryEventType.ILLNESS,
            impact=EventImpact.LOW,
        )
    )

    assert policy is None


def test_significant_illness_creates_return_period() -> None:
    policy = build_return_to_training_policy(
        create_event(
            event_type=TrajectoryEventType.ILLNESS,
            impact=EventImpact.HIGH,
        )
    )

    assert policy is not None
    assert policy.minimum_weeks == 2


def test_short_training_break_does_not_require_rebuild() -> None:
    policy = build_return_to_training_policy(
        create_event(
            event_type=TrajectoryEventType.TRAINING_BREAK,
            impact=EventImpact.MODERATE,
            start_day=1,
            end_day=7,
        )
    )

    assert policy is None


def test_two_week_training_break_requires_return_week() -> None:
    policy = build_return_to_training_policy(
        create_event(
            event_type=TrajectoryEventType.TRAINING_BREAK,
            impact=EventImpact.MODERATE,
            start_day=1,
            end_day=14,
        )
    )

    assert policy is not None
    assert policy.minimum_weeks == 1


def test_long_training_break_requires_longer_rebuild() -> None:
    policy = build_return_to_training_policy(
        create_event(
            event_type=TrajectoryEventType.TRAINING_BREAK,
            impact=EventImpact.HIGH,
            start_day=1,
            end_day=31,
        )
    )

    assert policy is not None
    assert policy.minimum_weeks == 3
