from datetime import date

import pytest

from opencoach.planning.trajectory_event import (
    EventImpact,
    RacePriority,
    TrajectoryEvent,
    TrajectoryEventType,
)


def test_a_race_can_be_declared() -> None:
    event = TrajectoryEvent(
        event_id="main-race",
        event_type=TrajectoryEventType.RACE,
        start_date=date(2027, 7, 10),
        end_date=date(2027, 7, 10),
        impact=EventImpact.HIGH,
        race_priority=RacePriority.A,
    )

    assert event.race_priority is RacePriority.A


def test_b_race_can_be_declared() -> None:
    event = TrajectoryEvent(
        event_id="preparation-race",
        event_type=TrajectoryEventType.RACE,
        start_date=date(2027, 5, 15),
        end_date=date(2027, 5, 15),
        impact=EventImpact.MODERATE,
        race_priority=RacePriority.B,
    )

    assert event.race_priority is RacePriority.B


def test_athlete_can_impose_unavailability() -> None:
    event = TrajectoryEvent(
        event_id="professional-duty",
        event_type=TrajectoryEventType.UNAVAILABILITY,
        start_date=date(2027, 4, 5),
        end_date=date(2027, 4, 7),
        impact=EventImpact.MODERATE,
        athlete_imposed=True,
    )

    assert event.athlete_imposed is True


def test_race_requires_priority() -> None:
    with pytest.raises(
        ValueError,
        match="priorité",
    ):
        TrajectoryEvent(
            event_id="race",
            event_type=TrajectoryEventType.RACE,
            start_date=date(2027, 6, 1),
            end_date=date(2027, 6, 1),
            impact=EventImpact.HIGH,
        )


def test_non_race_cannot_have_race_priority() -> None:
    with pytest.raises(
        ValueError,
        match="réservée",
    ):
        TrajectoryEvent(
            event_id="illness",
            event_type=TrajectoryEventType.ILLNESS,
            start_date=date(2027, 4, 1),
            end_date=date(2027, 4, 3),
            impact=EventImpact.MODERATE,
            race_priority=RacePriority.B,
        )


def test_event_end_cannot_precede_start() -> None:
    with pytest.raises(
        ValueError,
        match="précéder",
    ):
        TrajectoryEvent(
            event_id="invalid",
            event_type=TrajectoryEventType.TRAINING_BREAK,
            start_date=date(2027, 4, 10),
            end_date=date(2027, 4, 5),
            impact=EventImpact.MODERATE,
        )


def test_event_id_cannot_be_empty() -> None:
    with pytest.raises(
        ValueError,
        match="identifiant",
    ):
        TrajectoryEvent(
            event_id=" ",
            event_type=TrajectoryEventType.ILLNESS,
            start_date=date(2027, 4, 1),
            end_date=date(2027, 4, 2),
            impact=EventImpact.LOW,
        )
