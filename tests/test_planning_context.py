from dataclasses import FrozenInstanceError
from datetime import date
from uuid import uuid4

import pytest

from opencoach.models import AthleteProfile, Race
from opencoach.planning import PlanningContext


def create_race(
    *,
    name: str,
    priority: str,
) -> Race:
    return Race(
        id=uuid4(),
        date=date(2026, 10, 18),
        name=name,
        location="Test",
        race_type="trail",
        priority=priority,
        distance_km=42.0,
        elevation_gain_m=2000.0,
    )


def test_planning_context_can_be_created() -> None:
    athlete = AthleteProfile()

    primary_race = create_race(
        name="Objectif principal",
        priority="primary",
    )

    training_race = create_race(
        name="Course préparatoire",
        priority="training",
    )

    context = PlanningContext(
        planning_date=date(2026, 8, 22),
        athlete=athlete,
        primary_race=primary_race,
        training_races=(training_race,),
        readiness=None,
        recent_load=None,
        recent_stats=None,
    )

    assert context.planning_date == date(
        2026,
        8,
        22,
    )

    assert context.athlete is athlete
    assert context.primary_race is primary_race

    assert context.training_races == (
        training_race,
    )

    assert context.readiness is None
    assert context.recent_load is None
    assert context.recent_stats is None


def test_planning_context_supports_missing_optional_data() -> None:
    context = PlanningContext(
        planning_date=date(2026, 8, 22),
        athlete=AthleteProfile(),
        primary_race=None,
        training_races=(),
        readiness=None,
        recent_load=None,
        recent_stats=None,
    )

    assert context.primary_race is None
    assert context.training_races == ()
    assert context.readiness is None
    assert context.recent_load is None
    assert context.recent_stats is None


def test_planning_context_is_frozen() -> None:
    context = PlanningContext(
        planning_date=date(2026, 8, 22),
        athlete=AthleteProfile(),
        primary_race=None,
        training_races=(),
        readiness=None,
        recent_load=None,
        recent_stats=None,
    )

    with pytest.raises(FrozenInstanceError):
        context.primary_race = create_race(
            name="Nouvel objectif",
            priority="primary",
        )
