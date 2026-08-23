import pytest

from opencoach.planning.race_demand_profile import (
    ElevationDemand,
    RaceDistanceCategory,
    RaceSpecificityDemand,
    build_race_demand_profile,
    classify_distance,
    classify_elevation,
)


def test_short_distance_is_classified() -> None:
    assert (
        classify_distance(10.0)
        is RaceDistanceCategory.SHORT
    )


def test_middle_distance_is_classified() -> None:
    assert (
        classify_distance(30.0)
        is RaceDistanceCategory.MIDDLE
    )


def test_long_distance_is_classified() -> None:
    assert (
        classify_distance(50.0)
        is RaceDistanceCategory.LONG
    )


def test_ultra_distance_is_classified() -> None:
    assert (
        classify_distance(80.0)
        is RaceDistanceCategory.ULTRA
    )


def test_50k_2500m_has_very_high_elevation_demand() -> None:
    profile = build_race_demand_profile(
        distance_km=50.0,
        elevation_gain_m=2500.0,
    )

    assert (
        profile.elevation_demand
        is ElevationDemand.VERY_HIGH
    )

    assert (
        profile.elevation_ratio_m_per_km
        == pytest.approx(50.0)
    )


def test_long_trail_prioritizes_long_endurance() -> None:
    profile = build_race_demand_profile(
        distance_km=50.0,
        elevation_gain_m=2500.0,
    )

    assert (
        profile.long_endurance_demand
        is RaceSpecificityDemand.HIGH
    )


def test_long_mountain_trail_prioritizes_uphill_and_downhill() -> None:
    profile = build_race_demand_profile(
        distance_km=50.0,
        elevation_gain_m=2500.0,
    )

    assert (
        profile.uphill_demand
        is RaceSpecificityDemand.VERY_HIGH
    )

    assert (
        profile.downhill_demand
        is RaceSpecificityDemand.VERY_HIGH
    )


def test_short_race_prioritizes_threshold_more_than_ultra() -> None:
    short_profile = build_race_demand_profile(
        distance_km=10.0,
        elevation_gain_m=0.0,
    )

    ultra_profile = build_race_demand_profile(
        distance_km=100.0,
        elevation_gain_m=5000.0,
    )

    assert (
        short_profile.threshold_demand
        is RaceSpecificityDemand.VERY_HIGH
    )

    assert (
        ultra_profile.threshold_demand
        is RaceSpecificityDemand.LOW
    )


def test_ultra_has_very_high_long_endurance_demand() -> None:
    profile = build_race_demand_profile(
        distance_km=100.0,
        elevation_gain_m=5000.0,
    )

    assert (
        profile.long_endurance_demand
        is RaceSpecificityDemand.VERY_HIGH
    )


def test_invalid_distance_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="strictement positive",
    ):
        classify_distance(0.0)


def test_negative_elevation_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="ne peut pas être négatif",
    ):
        classify_elevation(
            distance_km=50.0,
            elevation_gain_m=-1.0,
        )
