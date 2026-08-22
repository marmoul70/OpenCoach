from opencoach.models import AthleteProfile
from opencoach.planning import (
    AthleteCapacityAssessment,
    compare_capacity_to_profile,
)


def create_capacity(
    *,
    weekly_sessions: float = 4.0,
    weekly_duration_minutes: float = 300.0,
    weekly_distance_km: float = 45.0,
) -> AthleteCapacityAssessment:
    return AthleteCapacityAssessment(
        weekly_sessions=weekly_sessions,
        weekly_duration_minutes=(
            weekly_duration_minutes
        ),
        weekly_distance_km=weekly_distance_km,
        weekly_elevation_gain_m=1200.0,
        weekly_training_load=280.0,
        longest_duration_minutes=150.0,
        longest_distance_km=24.0,
        highest_elevation_gain_m=1500.0,
        volume_trend="stable",
        confidence="high",
        reasons=(),
    )


def create_athlete(
    *,
    sessions: int | None = 4,
    duration_minutes: int | None = 300,
    distance_km: float | None = 45.0,
) -> AthleteProfile:
    athlete = AthleteProfile()

    athlete.training.weekly_sessions = sessions

    athlete.training.weekly_duration_minutes = (
        duration_minutes
    )

    athlete.training.weekly_distance_km = (
        distance_km
    )

    return athlete


def test_aligned_profile_and_capacity() -> None:
    comparison = compare_capacity_to_profile(
        athlete=create_athlete(),
        capacity=create_capacity(),
    )

    assert comparison.sessions.status == (
        "aligned"
    )

    assert comparison.duration_minutes.status == (
        "aligned"
    )

    assert comparison.distance_km.status == (
        "aligned"
    )

    assert comparison.has_mismatch is False


def test_capacity_below_declared_profile() -> None:
    comparison = compare_capacity_to_profile(
        athlete=create_athlete(
            sessions=5,
            duration_minutes=360,
            distance_km=55.0,
        ),
        capacity=create_capacity(
            weekly_sessions=4.0,
            weekly_duration_minutes=260.0,
            weekly_distance_km=42.0,
        ),
    )

    assert comparison.sessions.status == (
        "below_declared"
    )

    assert comparison.duration_minutes.status == (
        "below_declared"
    )

    assert comparison.distance_km.status == (
        "below_declared"
    )

    assert comparison.has_mismatch is True


def test_capacity_above_declared_profile() -> None:
    comparison = compare_capacity_to_profile(
        athlete=create_athlete(
            sessions=3,
            duration_minutes=240,
            distance_km=35.0,
        ),
        capacity=create_capacity(
            weekly_sessions=4.0,
            weekly_duration_minutes=300.0,
            weekly_distance_km=45.0,
        ),
    )

    assert comparison.sessions.status == (
        "above_declared"
    )

    assert comparison.duration_minutes.status == (
        "above_declared"
    )

    assert comparison.distance_km.status == (
        "above_declared"
    )

    assert comparison.has_mismatch is True


def test_missing_declared_values_are_unknown() -> None:
    comparison = compare_capacity_to_profile(
        athlete=create_athlete(
            sessions=None,
            duration_minutes=None,
            distance_km=None,
        ),
        capacity=create_capacity(),
    )

    assert comparison.sessions.status == (
        "unknown"
    )

    assert comparison.duration_minutes.status == (
        "unknown"
    )

    assert comparison.distance_km.status == (
        "unknown"
    )

    assert comparison.has_mismatch is False


def test_ratio_is_calculated() -> None:
    comparison = compare_capacity_to_profile(
        athlete=create_athlete(
            duration_minutes=360,
        ),
        capacity=create_capacity(
            weekly_duration_minutes=300.0,
        ),
    )

    assert (
        comparison.duration_minutes.ratio
        == 0.833
    )


def test_reasons_explain_profile_mismatch() -> None:
    comparison = compare_capacity_to_profile(
        athlete=create_athlete(
            duration_minutes=360,
        ),
        capacity=create_capacity(
            weekly_duration_minutes=250.0,
        ),
    )

    assert any(
        "durée hebdomadaire"
        in reason
        for reason in comparison.reasons
    )
