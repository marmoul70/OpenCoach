from uuid import uuid4
from datetime import date

import pytest

from opencoach.models import Race
from opencoach.planning import (
    RaceClassificationThresholds,
    classify_race_for_knowledge,
)


def create_thresholds():
    return RaceClassificationThresholds(
        road_short_max_km=12.0,
        road_middle_max_km=25.0,
        road_long_max_km=45.0,
        trail_short_max_km=25.0,
        trail_middle_max_km=50.0,
        trail_long_max_km=80.0,
        rolling_elevation_ratio=20.0,
        mountain_elevation_ratio=50.0,
    )


def create_race(
    *,
    race_type="trail",
    distance_km=50.0,
    elevation_gain_m=2500.0,
):
    return Race(
        id=uuid4(),
        date=date(
            2027,
            6,
            12,
        ),
        name="Test",
        location="Test",
        race_type=race_type,
        priority="primary",
        distance_km=distance_km,
        elevation_gain_m=elevation_gain_m,
        status="planned",
    )


def test_long_trail_is_classified_for_knowledge() -> None:
    result = classify_race_for_knowledge(
        race=create_race(),
        thresholds=create_thresholds(),
    )

    assert result.sport_family == "trail"

    assert result.distance_family == "middle"

    assert (
        "long_trail"
        in result.applicabilities
    )


def test_ultra_trail_is_detected() -> None:
    result = classify_race_for_knowledge(
        race=create_race(
            distance_km=100.0,
            elevation_gain_m=5000.0,
        ),
        thresholds=create_thresholds(),
    )

    assert result.distance_family == "ultra"

    assert (
        "ultra_trail"
        in result.applicabilities
    )


def test_road_short_race_maps_to_10k_knowledge() -> None:
    result = classify_race_for_knowledge(
        race=create_race(
            race_type="road",
            distance_km=10.0,
            elevation_gain_m=50.0,
        ),
        thresholds=create_thresholds(),
    )

    assert (
        "10k"
        in result.applicabilities
    )


def test_elevation_profile_uses_ratio() -> None:
    result = classify_race_for_knowledge(
        race=create_race(
            distance_km=50.0,
            elevation_gain_m=2500.0,
        ),
        thresholds=create_thresholds(),
    )

    assert (
        result.elevation_profile
        == "mountain"
    )


def test_missing_elevation_is_unknown() -> None:
    result = classify_race_for_knowledge(
        race=create_race(
            elevation_gain_m=None,
        ),
        thresholds=create_thresholds(),
    )

    assert (
        result.elevation_profile
        == "unknown"
    )


def test_invalid_thresholds_are_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="route",
    ):
        RaceClassificationThresholds(
            road_short_max_km=20.0,
            road_middle_max_km=10.0,
            road_long_max_km=40.0,
            trail_short_max_km=25.0,
            trail_middle_max_km=50.0,
            trail_long_max_km=80.0,
            rolling_elevation_ratio=20.0,
            mountain_elevation_ratio=50.0,
        )

def test_unknown_sport_is_not_classified_as_road_running() -> None:
    result = classify_race_for_knowledge(
        race=create_race(
            race_type="cycling",
            distance_km=100.0,
            elevation_gain_m=1200.0,
        ),
        thresholds=create_thresholds(),
    )

    assert result.sport_family == "other"

    assert result.distance_family == "unknown"

    assert (
        "road_running"
        not in result.applicabilities
    )

    assert (
        "10k"
        not in result.applicabilities
    )

    assert (
        "half_marathon"
        not in result.applicabilities
    )

    assert (
        "marathon"
        not in result.applicabilities
    )