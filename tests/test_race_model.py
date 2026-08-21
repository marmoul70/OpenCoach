from datetime import date
from uuid import uuid4

from opencoach.models import Race


def test_race_can_represent_primary_goal() -> None:
    race = Race(
        id=uuid4(),
        date=date(
            2027,
            7,
            10,
        ),
        name="Ultra objectif",
        location="Jura",
        race_type="trail",
        priority="primary",
        distance_km=65.0,
        elevation_gain_m=3100.0,
        target_time_minutes=600,
    )

    assert race.priority == "primary"
    assert race.status == "planned"

    assert race.distance_km == 65.0
    assert race.elevation_gain_m == 3100.0

    assert race.actual_distance_km is None
    assert race.activity_id is None


def test_race_can_store_manual_abandon_result() -> None:
    race = Race(
        id=uuid4(),
        date=date(
            2027,
            5,
            15,
        ),
        name="Trail préparation",
        location="Vosges",
        race_type="trail",
        priority="training",
        distance_km=50.0,
        elevation_gain_m=2500.0,
        status="abandoned",
        actual_distance_km=31.7,
        actual_elevation_gain_m=1600.0,
        actual_time_minutes=280,
    )

    assert race.status == "abandoned"

    assert race.distance_km == 50.0
    assert race.actual_distance_km == 31.7


def test_race_can_reference_activity() -> None:
    activity_id = uuid4()

    race = Race(
        id=uuid4(),
        date=date(
            2027,
            4,
            18,
        ),
        name="Trail préparation",
        location="Jura",
        race_type="trail",
        priority="training",
        distance_km=30.0,
        activity_id=activity_id,
    )

    assert race.activity_id == activity_id
