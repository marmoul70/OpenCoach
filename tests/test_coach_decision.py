from datetime import date

from opencoach.coaching import (
    decide_training_session,
)
from opencoach.config import (
    load_threshold_settings,
)
from opencoach.models import TrainingSession
from opencoach.readiness import DailyReadiness


def create_session(
    *,
    duration_minutes: int = 60,
    intensity: str = "high",
) -> TrainingSession:
    return TrainingSession(
        id=None,
        date=date(
            2026,
            8,
            18,
        ),
        type="intervals",
        sport_type="Run",
        title="Fractionné",
        description="Séance qualitative.",
        duration_minutes=duration_minutes,
        intensity=intensity,
    )


def create_readiness(
    *,
    score: float,
    constraints: tuple[str, ...] = (),
) -> DailyReadiness:
    return DailyReadiness(
        score=score,
        level="moderate",
        signals=(),
        warning_count=0,
        critical_count=0,
        training_constraints=constraints,
        fitness_ctl=40.0,
        fatigue_atl=35.0,
        training_balance=5.0,
    )


def thresholds():
    return (
        load_threshold_settings()
        .coach_decision
    )


def test_coach_decision_keeps_session_when_ready() -> None:
    decision = decide_training_session(
        session=create_session(),
        readiness=create_readiness(
            score=90.0,
        ),
        thresholds=thresholds(),
    )

    assert decision.action == "keep"

    assert (
        decision.recommended_duration_minutes
        == 60
    )

    assert decision.duration_factor == 1.0
    assert decision.intensity_factor == 1.0

    assert (
        decision.recommended_intensity
        == "high"
    )


def test_coach_decision_reduces_session() -> None:
    decision = decide_training_session(
        session=create_session(),
        readiness=create_readiness(
            score=60.0,
        ),
        thresholds=thresholds(),
    )

    assert decision.action == "reduce"

    assert (
        decision.recommended_duration_minutes
        == 42
    )

    assert decision.duration_factor == 0.7
    assert decision.intensity_factor == 0.8


def test_coach_decision_reduces_more_when_high_intensity_is_forbidden() -> None:
    decision = decide_training_session(
        session=create_session(),
        readiness=create_readiness(
            score=60.0,
            constraints=(
                "avoid_high_intensity",
            ),
        ),
        thresholds=thresholds(),
    )

    assert decision.action == "reduce"

    assert decision.duration_factor == 0.595

    assert (
        decision.recommended_duration_minutes
        == 36
    )

    assert (
        decision.recommended_intensity
        == "easy"
    )


def test_coach_decision_replaces_session() -> None:
    decision = decide_training_session(
        session=create_session(
            duration_minutes=75,
        ),
        readiness=create_readiness(
            score=40.0,
        ),
        thresholds=thresholds(),
    )

    assert decision.action == "replace"

    assert (
        decision.recommended_duration_minutes
        == 45
    )

    assert (
        decision.recommended_intensity
        == "very_easy"
    )


def test_coach_decision_rests_when_score_is_very_low() -> None:
    decision = decide_training_session(
        session=create_session(),
        readiness=create_readiness(
            score=20.0,
        ),
        thresholds=thresholds(),
    )

    assert decision.action == "rest"

    assert (
        decision.recommended_duration_minutes
        is None
    )

    assert (
        decision.recommended_intensity
        is None
    )


def test_recovery_constraint_can_force_rest() -> None:
    decision = decide_training_session(
        session=create_session(),
        readiness=create_readiness(
            score=40.0,
            constraints=(
                "prefer_recovery_or_rest",
            ),
        ),
        thresholds=thresholds(),
    )

    assert decision.action == "rest"


def test_score_at_keep_boundary_keeps_session() -> None:
    decision = decide_training_session(
        session=create_session(),
        readiness=create_readiness(
            score=70.0,
        ),
        thresholds=thresholds(),
    )

    assert decision.action == "keep"


def test_score_at_reduce_boundary_reduces_session() -> None:
    decision = decide_training_session(
        session=create_session(),
        readiness=create_readiness(
            score=50.0,
        ),
        thresholds=thresholds(),
    )

    assert decision.action == "reduce"


def test_score_at_replace_boundary_replaces_session() -> None:
    decision = decide_training_session(
        session=create_session(),
        readiness=create_readiness(
            score=30.0,
        ),
        thresholds=thresholds(),
    )

    assert decision.action == "replace"