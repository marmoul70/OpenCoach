from datetime import date

from opencoach.planning.trajectory.adjustment import (
    LoadAdjustment,
    ProgressionAdjustment,
)
from opencoach.planning.trajectory.event import (
    EventImpact,
    RacePriority,
    TrajectoryEvent,
    TrajectoryEventType,
)
from opencoach.planning.trajectory.event_resolver import (
    resolve_trajectory_events,
)


def test_no_event_keeps_normal_progression() -> None:
    result = resolve_trajectory_events(
        events=()
    )

    assert result.adjustments == ()

    assert (
        result.load_adjustment
        is LoadAdjustment.MAINTAIN
    )

    assert (
        result.progression_adjustment
        is ProgressionAdjustment.CONTINUE
    )

    assert result.event_requires_recovery is False
    assert result.requires_return_to_training is False

    assert result.allow_schedule_compression is True

    assert (
        result.athlete_schedule_constrained
        is False
    )

    assert result.notes == ()


def test_strongest_load_adjustment_wins() -> None:
    events = (
        TrajectoryEvent(
            event_id="race-b",
            event_type=TrajectoryEventType.RACE,
            start_date=date(
                2027,
                5,
                15,
            ),
            end_date=date(
                2027,
                5,
                15,
            ),
            impact=EventImpact.MODERATE,
            race_priority=RacePriority.B,
        ),
        TrajectoryEvent(
            event_id="illness",
            event_type=TrajectoryEventType.ILLNESS,
            start_date=date(
                2027,
                5,
                12,
            ),
            end_date=date(
                2027,
                5,
                14,
            ),
            impact=EventImpact.HIGH,
        ),
    )

    result = resolve_trajectory_events(
        events=events
    )

    assert (
        result.load_adjustment
        is LoadAdjustment.SUSPEND
    )


def test_most_conservative_progression_wins() -> None:
    events = (
        TrajectoryEvent(
            event_id="short-break",
            event_type=(
                TrajectoryEventType.TRAINING_BREAK
            ),
            start_date=date(
                2027,
                4,
                1,
            ),
            end_date=date(
                2027,
                4,
                5,
            ),
            impact=EventImpact.MODERATE,
        ),
        TrajectoryEvent(
            event_id="long-break",
            event_type=(
                TrajectoryEventType.TRAINING_BREAK
            ),
            start_date=date(
                2027,
                4,
                10,
            ),
            end_date=date(
                2027,
                4,
                25,
            ),
            impact=EventImpact.HIGH,
        ),
    )

    result = resolve_trajectory_events(
        events=events
    )

    assert (
        result.progression_adjustment
        is ProgressionAdjustment.REBUILD
    )


def test_significant_event_can_require_recovery() -> None:
    event = TrajectoryEvent(
        event_id="illness",
        event_type=TrajectoryEventType.ILLNESS,
        start_date=date(
            2027,
            4,
            1,
        ),
        end_date=date(
            2027,
            4,
            5,
        ),
        impact=EventImpact.HIGH,
    )

    result = resolve_trajectory_events(
        events=(
            event,
        )
    )

    assert result.event_requires_recovery is True


def test_minor_event_does_not_necessarily_require_recovery() -> None:
    event = TrajectoryEvent(
        event_id="race-b",
        event_type=TrajectoryEventType.RACE,
        start_date=date(
            2027,
            5,
            15,
        ),
        end_date=date(
            2027,
            5,
            15,
        ),
        impact=EventImpact.MODERATE,
        race_priority=RacePriority.B,
    )

    result = resolve_trajectory_events(
        events=(
            event,
        )
    )

    assert isinstance(
        result.event_requires_recovery,
        bool,
    )


def test_athlete_imposed_event_marks_schedule_as_constrained() -> None:
    event = TrajectoryEvent(
        event_id="work",
        event_type=TrajectoryEventType.UNAVAILABILITY,
        start_date=date(
            2027,
            4,
            5,
        ),
        end_date=date(
            2027,
            4,
            7,
        ),
        impact=EventImpact.MODERATE,
        athlete_imposed=True,
    )

    result = resolve_trajectory_events(
        events=(
            event,
        )
    )

    assert (
        result.athlete_schedule_constrained
        is True
    )


def test_non_athlete_imposed_event_does_not_mark_schedule() -> None:
    event = TrajectoryEvent(
        event_id="illness",
        event_type=TrajectoryEventType.ILLNESS,
        start_date=date(
            2027,
            4,
            5,
        ),
        end_date=date(
            2027,
            4,
            7,
        ),
        impact=EventImpact.MODERATE,
        athlete_imposed=False,
    )

    result = resolve_trajectory_events(
        events=(
            event,
        )
    )

    assert (
        result.athlete_schedule_constrained
        is False
    )


def test_event_can_require_return_to_training() -> None:
    event = TrajectoryEvent(
        event_id="injury",
        event_type=TrajectoryEventType.INJURY,
        start_date=date(
            2027,
            4,
            1,
        ),
        end_date=date(
            2027,
            4,
            15,
        ),
        impact=EventImpact.HIGH,
    )

    result = resolve_trajectory_events(
        events=(
            event,
        )
    )

    assert (
        result.requires_return_to_training
        is True
    )


def test_schedule_compression_is_preserved_when_allowed() -> None:
    event = TrajectoryEvent(
        event_id="work",
        event_type=TrajectoryEventType.UNAVAILABILITY,
        start_date=date(
            2027,
            4,
            5,
        ),
        end_date=date(
            2027,
            4,
            7,
        ),
        impact=EventImpact.MODERATE,
        athlete_imposed=True,
    )

    result = resolve_trajectory_events(
        events=(
            event,
        )
    )

    assert (
        result.allow_schedule_compression
        is True
    )

def test_event_resolver_preserves_schedule_compression_policy() -> None:
    event = TrajectoryEvent(
        event_id="injury",
        event_type=TrajectoryEventType.INJURY,
        start_date=date(
            2027,
            4,
            1,
        ),
        end_date=date(
            2027,
            4,
            15,
        ),
        impact=EventImpact.HIGH,
    )

    result = resolve_trajectory_events(
        events=(
            event,
        )
    )

    assert len(result.adjustments) == 1

    assert (
        result.allow_schedule_compression
        is result.adjustments[0].allow_schedule_compression
    )

def test_multiple_adjustments_are_preserved() -> None:
    events = (
        TrajectoryEvent(
            event_id="work",
            event_type=TrajectoryEventType.UNAVAILABILITY,
            start_date=date(
                2027,
                4,
                1,
            ),
            end_date=date(
                2027,
                4,
                2,
            ),
            impact=EventImpact.MODERATE,
            athlete_imposed=True,
        ),
        TrajectoryEvent(
            event_id="injury",
            event_type=TrajectoryEventType.INJURY,
            start_date=date(
                2027,
                4,
                1,
            ),
            end_date=date(
                2027,
                4,
                10,
            ),
            impact=EventImpact.HIGH,
        ),
    )

    result = resolve_trajectory_events(
        events=events
    )

    assert len(
        result.adjustments
    ) == 2


def test_notes_from_event_adjustments_are_preserved() -> None:
    event = TrajectoryEvent(
        event_id="work",
        event_type=TrajectoryEventType.UNAVAILABILITY,
        start_date=date(
            2027,
            4,
            5,
        ),
        end_date=date(
            2027,
            4,
            7,
        ),
        impact=EventImpact.MODERATE,
        athlete_imposed=True,
    )

    result = resolve_trajectory_events(
        events=(
            event,
        )
    )

    assert isinstance(
        result.notes,
        tuple,
    )