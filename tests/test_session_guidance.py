from datetime import date
from uuid import uuid4

import pytest

from opencoach.coaching.session_guidance import (
    build_session_guidance,
)
from opencoach.models import TrainingSession


def session(
    session_type: str,
    *,
    description: str = "",
    intensity: str = "moderate",
    heart_rate_zone: str | None = None,
) -> TrainingSession:
    return TrainingSession(
        id=uuid4(),
        date=date(
            2026,
            8,
            28,
        ),
        type=session_type,
        sport_type="Run",
        title=session_type,
        description=description,
        duration_minutes=60,
        intensity=intensity,
        heart_rate_zone=heart_rate_zone,
    )


@pytest.mark.parametrize(
    "session_type",
    (
        "aerobic_easy",
        "long_endurance",
        "threshold",
        "vo2max",
        "speed_development",
        "strength_lower_body",
        "rest",
        "supplementary",
    ),
)
def test_known_session_types_have_guidance(
    session_type: str,
) -> None:
    guidance = build_session_guidance(
        session(
            session_type
        )
    )

    assert guidance.objective
    assert guidance.coach_rationale
    assert guidance.main_set
    assert guidance.analysis_targets


def test_threshold_explains_warmup_and_cooldown() -> None:
    guidance = build_session_guidance(
        session(
            "threshold",
            heart_rate_zone="Z4",
        )
    )

    assert guidance.warmup
    assert guidance.cooldown

    assert (
        guidance.main_set[0]
        .heart_rate_target
        == "Z4"
    )


def test_existing_generated_description_is_preserved() -> None:
    guidance = build_session_guidance(
        session(
            "vo2max",
            description=(
                "6 × 3 min à haute intensité, "
                "récupération 2 min."
            ),
        )
    )

    assert (
        "6 × 3 min"
        in guidance.main_set[
            0
        ].description
    )


def test_easy_session_explains_low_intensity_goal() -> None:
    guidance = build_session_guidance(
        session(
            "aerobic_easy"
        )
    )

    assert (
        "endurance"
        in guidance.objective.lower()
    )

    assert (
        "heart_rate_drift"
        in guidance.analysis_targets
    )


def test_long_endurance_includes_nutrition_analysis() -> None:
    guidance = build_session_guidance(
        session(
            "long_endurance"
        )
    )

    assert (
        "nutrition"
        in guidance.analysis_targets
    )


def test_unknown_session_type_uses_safe_fallback() -> None:
    guidance = build_session_guidance(
        session(
            "future_new_session"
        )
    )

    assert (
        guidance.session_type
        == "future_new_session"
    )

    assert guidance.main_set


def test_guidance_exposes_structured_intensity_targets() -> None:
    training_session = session(
        "aerobic_easy"
    )

    training_session.prescription = {
        "intensity": {
            "targets": [
                {
                    "reference": "heart_rate",
                    "label": "Fréquence cardiaque",
                    "minimum": 129,
                    "maximum": 152,
                    "unit": "bpm",
                },
                {
                    "reference": "vma_percent",
                    "label": "Pourcentage de VMA",
                    "minimum": 60,
                    "maximum": 70,
                    "unit": "% VMA",
                    "derived": {
                        "vma_kmh": 15.0,
                        "speed_kmh": {
                            "minimum": 9.0,
                            "maximum": 10.5,
                        },
                        "pace_seconds_per_km": {
                            "fastest": 342.857,
                            "slowest": 400.0,
                        },
                    },
                },
                {
                    "reference": "rpe",
                    "label": "Perception de l'effort",
                    "minimum": 2,
                    "maximum": 3,
                    "unit": "/10",
                },
            ],
        },
    }

    guidance = build_session_guidance(
        training_session
    )

    targets = (
        guidance.main_set[
            0
        ].intensity_targets
    )

    assert len(targets) == 3

    heart_rate = targets[0]

    assert (
        heart_rate.reference
        == "heart_rate"
    )
    assert heart_rate.minimum == 129
    assert heart_rate.maximum == 152
    assert heart_rate.unit == "bpm"

    vma = targets[1]

    assert (
        vma.reference
        == "vma_percent"
    )
    assert vma.minimum == 60
    assert vma.maximum == 70

    assert (
        vma.speed_min_kmh
        == 9.0
    )
    assert (
        vma.speed_max_kmh
        == 10.5
    )

    assert (
        vma.pace_slowest_seconds_per_km
        == 400.0
    )

    assert (
        round(
            vma.pace_fastest_seconds_per_km
        )
        == 343
    )

    rpe = targets[2]

    assert rpe.reference == "rpe"
    assert rpe.minimum == 2
    assert rpe.maximum == 3
