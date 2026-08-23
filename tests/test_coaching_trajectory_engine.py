from datetime import date

from opencoach.planning.trajectory.engine import (
    CoachingTrajectoryEngine,
)
from opencoach.planning.trajectory.adjustment import (
    AdjustmentSeverity,
    LoadAdjustment,
    ProgressionAdjustment,
)
from opencoach.planning.trajectory.event import (
    EventImpact,
    RacePriority,
    TrajectoryEvent,
    TrajectoryEventType,
)


def create_engine() -> CoachingTrajectoryEngine:
    return CoachingTrajectoryEngine()


def test_a_race_reduces_load_and_pauses_progression() -> None:
    event = TrajectoryEvent(
        event_id="race-a",
        event_type=TrajectoryEventType.RACE,
        start_date=date(2027, 7, 10),
        end_date=date(2027, 7, 10),
        impact=EventImpact.HIGH,
        race_priority=RacePriority.A,
    )

    adjustment = create_engine().adjust_for_event(event)

    assert adjustment.load is LoadAdjustment.REDUCE
    assert adjustment.progression is ProgressionAdjustment.PAUSE


def test_b_race_does_not_stop_main_progression() -> None:
    event = TrajectoryEvent(
        event_id="race-b",
        event_type=TrajectoryEventType.RACE,
        start_date=date(2027, 5, 15),
        end_date=date(2027, 5, 15),
        impact=EventImpact.MODERATE,
        race_priority=RacePriority.B,
    )

    adjustment = create_engine().adjust_for_event(event)

    assert adjustment.load is LoadAdjustment.REDUCE_SLIGHTLY

    assert (
        adjustment.progression
        is ProgressionAdjustment.CONTINUE
    )


def test_c_race_can_be_integrated_as_training() -> None:
    event = TrajectoryEvent(
        event_id="race-c",
        event_type=TrajectoryEventType.RACE,
        start_date=date(2027, 4, 10),
        end_date=date(2027, 4, 10),
        impact=EventImpact.LOW,
        race_priority=RacePriority.C,
    )

    adjustment = create_engine().adjust_for_event(event)

    assert adjustment.load is LoadAdjustment.MAINTAIN
    assert adjustment.severity is AdjustmentSeverity.MINOR


def test_professional_constraint_allows_compressed_week() -> None:
    event = TrajectoryEvent(
        event_id="work",
        event_type=TrajectoryEventType.UNAVAILABILITY,
        start_date=date(2027, 4, 5),
        end_date=date(2027, 4, 7),
        impact=EventImpact.MODERATE,
        athlete_imposed=True,
    )

    adjustment = create_engine().adjust_for_event(event)

    assert adjustment.allow_schedule_compression is True

    assert (
        adjustment.progression
        is ProgressionAdjustment.CONTINUE
    )


def test_high_schedule_constraint_can_reduce_load() -> None:
    event = TrajectoryEvent(
        event_id="work-heavy",
        event_type=TrajectoryEventType.UNAVAILABILITY,
        start_date=date(2027, 4, 5),
        end_date=date(2027, 4, 9),
        impact=EventImpact.HIGH,
        athlete_imposed=True,
    )

    adjustment = create_engine().adjust_for_event(event)

    assert adjustment.load is LoadAdjustment.REDUCE


def test_significant_illness_suspends_training() -> None:
    event = TrajectoryEvent(
        event_id="illness",
        event_type=TrajectoryEventType.ILLNESS,
        start_date=date(2027, 4, 5),
        end_date=date(2027, 4, 8),
        impact=EventImpact.HIGH,
    )

    adjustment = create_engine().adjust_for_event(event)

    assert adjustment.load is LoadAdjustment.SUSPEND
    assert adjustment.progression is ProgressionAdjustment.PAUSE
    assert adjustment.requires_return_to_training is True


def test_injury_requires_return_to_training() -> None:
    event = TrajectoryEvent(
        event_id="injury",
        event_type=TrajectoryEventType.INJURY,
        start_date=date(2027, 4, 5),
        end_date=date(2027, 4, 20),
        impact=EventImpact.HIGH,
    )

    adjustment = create_engine().adjust_for_event(event)

    assert adjustment.requires_return_to_training is True


def test_short_training_break_only_slows_progression() -> None:
    event = TrajectoryEvent(
        event_id="short-break",
        event_type=TrajectoryEventType.TRAINING_BREAK,
        start_date=date(2027, 4, 1),
        end_date=date(2027, 4, 5),
        impact=EventImpact.MODERATE,
    )

    adjustment = create_engine().adjust_for_event(event)

    assert adjustment.progression is ProgressionAdjustment.SLOW
    assert adjustment.requires_return_to_training is False


def test_long_training_break_rebuilds_progression() -> None:
    event = TrajectoryEvent(
        event_id="long-break",
        event_type=TrajectoryEventType.TRAINING_BREAK,
        start_date=date(2027, 4, 1),
        end_date=date(2027, 4, 20),
        impact=EventImpact.HIGH,
    )

    adjustment = create_engine().adjust_for_event(event)

    assert adjustment.progression is ProgressionAdjustment.REBUILD
    assert adjustment.requires_return_to_training is True
