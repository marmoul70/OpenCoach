import pytest

from opencoach.planning.knowledge.race_demand_profile import (
    build_race_demand_profile,
)
from opencoach.planning.weekly.volume_demand import (
    VolumeDemandPolicy,
    build_race_volume_demand,
)


def test_50k_mountain_race_requires_about_six_hours_peak() -> None:
    profile = build_race_demand_profile(
        distance_km=50.0,
        elevation_gain_m=2500.0,
    )

    demand = build_race_volume_demand(
        race_profile=profile
    )

    assert demand.effort_distance_km == pytest.approx(
        75.0
    )

    assert (
        demand.specific_peak_duration_minutes
        == pytest.approx(360.0)
    )


def test_70k_mountain_race_requires_about_seven_hours_peak() -> None:
    profile = build_race_demand_profile(
        distance_km=70.0,
        elevation_gain_m=3500.0,
    )

    demand = build_race_volume_demand(
        race_profile=profile
    )

    assert demand.effort_distance_km == pytest.approx(
        105.0
    )

    assert (
        demand.specific_peak_duration_minutes
        == pytest.approx(420.0)
    )


def test_100k_mountain_race_has_higher_volume_demand() -> None:
    profile = build_race_demand_profile(
        distance_km=100.0,
        elevation_gain_m=5000.0,
    )

    demand = build_race_volume_demand(
        race_profile=profile
    )

    assert demand.effort_distance_km == pytest.approx(
        150.0
    )

    assert (
        demand.specific_peak_duration_minutes
        == pytest.approx(510.0)
    )


def test_elevation_increases_volume_demand_for_same_distance() -> None:
    flat = build_race_volume_demand(
        race_profile=build_race_demand_profile(
            distance_km=50.0,
            elevation_gain_m=0.0,
        )
    )

    mountain = build_race_volume_demand(
        race_profile=build_race_demand_profile(
            distance_km=50.0,
            elevation_gain_m=2500.0,
        )
    )

    assert (
        mountain.specific_peak_duration_minutes
        > flat.specific_peak_duration_minutes
    )


def test_volume_demand_respects_upper_safety_bound() -> None:
    profile = build_race_demand_profile(
        distance_km=200.0,
        elevation_gain_m=10000.0,
    )

    demand = build_race_volume_demand(
        race_profile=profile
    )

    assert (
        demand.specific_peak_duration_minutes
        == 600.0
    )


def test_custom_policy_can_change_calibration() -> None:
    profile = build_race_demand_profile(
        distance_km=70.0,
        elevation_gain_m=3500.0,
    )

    demand = build_race_volume_demand(
        race_profile=profile,
        policy=VolumeDemandPolicy(
            base_minutes=180.0,
            minutes_per_effort_km=1.5,
            minimum_minutes=180.0,
            maximum_minutes=600.0,
        ),
    )

    assert (
        demand.specific_peak_duration_minutes
        == pytest.approx(337.5)
    )


def test_policy_rejects_invalid_bounds() -> None:
    with pytest.raises(ValueError):
        VolumeDemandPolicy(
            base_minutes=210.0,
            minutes_per_effort_km=2.0,
            minimum_minutes=600.0,
            maximum_minutes=300.0,
        )
