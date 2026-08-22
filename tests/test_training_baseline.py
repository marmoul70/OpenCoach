from opencoach.models import AthleteProfile
from opencoach.planning import (
    AthleteCapacityAssessment,
    CapacityMetricComparison,
    CapacityProfileComparison,
    build_training_baseline,
)


def create_athlete(
    *,
    sessions: int | None = 4,
    duration: int | None = 360,
    distance: float | None = 50.0,
) -> AthleteProfile:
    athlete = AthleteProfile()

    athlete.training.weekly_sessions = sessions
    athlete.training.weekly_duration_minutes = duration
    athlete.training.weekly_distance_km = distance

    return athlete


def create_capacity(
    *,
    confidence: str,
    sessions: float = 4.0,
    duration: float = 260.0,
    distance: float = 42.0,
) -> AthleteCapacityAssessment:
    return AthleteCapacityAssessment(
        weekly_sessions=sessions,
        weekly_duration_minutes=duration,
        weekly_distance_km=distance,
        weekly_elevation_gain_m=1200.0,
        weekly_training_load=280.0,
        longest_duration_minutes=160.0,
        longest_distance_km=25.0,
        highest_elevation_gain_m=1500.0,
        volume_trend="stable",
        confidence=confidence,
        reasons=(),
    )


def create_comparison(
    *,
    mismatch: bool,
) -> CapacityProfileComparison:
    status = (
        "below_declared"
        if mismatch
        else "aligned"
    )

    metric = CapacityMetricComparison(
        declared=360.0,
        demonstrated=260.0,
        status=status,
        ratio=0.722,
    )

    return CapacityProfileComparison(
        sessions=metric,
        duration_minutes=metric,
        distance_km=metric,
        reasons=(),
    )


def test_high_confidence_uses_demonstrated_capacity() -> None:
    baseline = build_training_baseline(
        athlete=create_athlete(
            sessions=5,
            duration=360,
            distance=55.0,
        ),
        capacity=create_capacity(
            confidence="high",
            sessions=4.0,
            duration=260.0,
            distance=42.0,
        ),
        comparison=create_comparison(
            mismatch=True
        ),
    )

    assert baseline.weekly_sessions == 4.0

    assert (
        baseline.weekly_duration_minutes
        == 260.0
    )

    assert baseline.weekly_distance_km == 42.0


def test_medium_confidence_uses_conservative_value() -> None:
    baseline = build_training_baseline(
        athlete=create_athlete(
            sessions=5,
            duration=360,
            distance=55.0,
        ),
        capacity=create_capacity(
            confidence="medium",
            sessions=4.0,
            duration=280.0,
            distance=44.0,
        ),
        comparison=create_comparison(
            mismatch=True
        ),
    )

    assert baseline.weekly_sessions == 4.0

    assert (
        baseline.weekly_duration_minutes
        == 280.0
    )

    assert baseline.weekly_distance_km == 44.0


def test_low_confidence_falls_back_to_profile_without_history() -> None:
    baseline = build_training_baseline(
        athlete=create_athlete(
            sessions=4,
            duration=300,
            distance=45.0,
        ),
        capacity=create_capacity(
            confidence="low",
            sessions=0.0,
            duration=0.0,
            distance=0.0,
        ),
        comparison=create_comparison(
            mismatch=False
        ),
    )

    assert baseline.weekly_sessions == 4.0

    assert (
        baseline.weekly_duration_minutes
        == 300.0
    )

    assert baseline.weekly_distance_km == 45.0


def test_low_confidence_does_not_exceed_demonstrated_when_both_exist() -> None:
    baseline = build_training_baseline(
        athlete=create_athlete(
            sessions=5,
            duration=360,
            distance=55.0,
        ),
        capacity=create_capacity(
            confidence="low",
            sessions=3.0,
            duration=220.0,
            distance=35.0,
        ),
        comparison=create_comparison(
            mismatch=True
        ),
    )

    assert baseline.weekly_sessions == 3.0

    assert (
        baseline.weekly_duration_minutes
        == 220.0
    )

    assert baseline.weekly_distance_km == 35.0


def test_preserves_trail_capacity_metrics() -> None:
    baseline = build_training_baseline(
        athlete=create_athlete(),
        capacity=create_capacity(
            confidence="high"
        ),
        comparison=create_comparison(
            mismatch=True
        ),
    )

    assert (
        baseline.weekly_elevation_gain_m
        == 1200.0
    )

    assert (
        baseline.weekly_training_load
        == 280.0
    )

    assert (
        baseline.longest_duration_minutes
        == 160.0
    )

    assert (
        baseline.longest_distance_km
        == 25.0
    )

    assert (
        baseline.highest_elevation_gain_m
        == 1500.0
    )


def test_reason_reports_profile_mismatch() -> None:
    baseline = build_training_baseline(
        athlete=create_athlete(),
        capacity=create_capacity(
            confidence="high"
        ),
        comparison=create_comparison(
            mismatch=True
        ),
    )

    assert any(
        "écart"
        in reason
        for reason in baseline.reasons
    )
