from datetime import date
from uuid import uuid4

import pytest

from opencoach.integrations.coros.workout_mapper import (
    CorosWorkoutMappingError,
    map_training_session_to_coros,
)
from opencoach.models import TrainingSession


def make_session(
    *,
    sport_type: str = "Run",
    status: str = "planned",
    prescription: dict | None = None,
    distance_km: float | None = None,
) -> TrainingSession:
    return TrainingSession(
        id=uuid4(),
        date=date(2026, 11, 12),
        type="aerobic_easy",
        sport_type=sport_type,
        title="Séance test OpenCoach",
        description="Objectif : développer l'endurance.",
        duration_minutes=50,
        distance_km=distance_km,
        intensity="easy",
        prescription=prescription,
        status=status,
    )


def heart_rate_prescription(
    work_structure: dict,
    *,
    minimum: int = 140,
    maximum: int = 155,
    blocks: list | None = None,
) -> dict:
    return {
        "version": 1,
        "blocks": blocks or [],
        "work_structure": work_structure,
        "intensity": {
            "targets": [
                {
                    "reference": "heart_rate",
                    "minimum": minimum,
                    "maximum": maximum,
                    "unit": "bpm",
                },
                {
                    "reference": "rpe",
                    "minimum": 2,
                    "maximum": 3,
                    "unit": "/10",
                },
            ],
        },
    }


def test_maps_continuous_run_with_warmup_main_and_cooldown() -> None:
    session = make_session(
        prescription=heart_rate_prescription(
            {
                "type": "continuous",
                "available_minutes": 30,
                "continuous_minutes": 30,
                "intervals": [],
            },
            blocks=[
                {"name": "Échauffement", "duration_minutes": 10},
                {"name": "Bloc principal", "duration_minutes": 30},
                {"name": "Retour au calme", "duration_minutes": 10},
            ],
        )
    )

    payload = map_training_session_to_coros(session)

    assert payload.date == "20261112"
    assert payload.course["sportType"] == 1
    assert payload.course["courseName"] == "Séance test OpenCoach"
    assert payload.course["sections"] == [
        {"sectionType": 1, "targetType": 2, "targetValue": 600},
        {
            "sectionType": 2,
            "targetType": 2,
            "targetValue": 1800,
            "intensityType": 1,
            "intensityValueStart": 140,
            "intensityValueEnd": 155,
        },
        {"sectionType": 4, "targetType": 2, "targetValue": 600},
    ]
    assert len(payload.payload_hash) == 64


def test_maps_repetitions_and_preserves_recovery_duration() -> None:
    session = make_session(
        prescription=heart_rate_prescription(
            {
                "type": "repeats",
                "available_minutes": 24,
                "intervals": [
                    {
                        "repetitions": 6,
                        "work_distance_meters": 400,
                        "work_duration": None,
                        "work_unit": None,
                        "repetition_target": {
                            "distance_meters": 400,
                            "fast_seconds": 90,
                            "slow_seconds": 96,
                        },
                        "recovery_duration": 90,
                        "recovery_unit": "seconds",
                    }
                ],
            }
        )
    )

    payload = map_training_session_to_coros(session)
    group = payload.course["sections"][0]

    assert group["intervalGroup"] is True
    assert group["repeats"] == 6
    assert group["sets"] == [
        {
            "sectionType": 2,
            "targetType": 1,
            "targetValue": 400,
            "intensityType": 2,
            "intensityValueStart": 225,
            "intensityValueEnd": 240,
        },
        {
            "sectionType": 3,
            "targetType": 2,
            "targetValue": 90,
        },
    ]


def test_maps_vma_target_to_absolute_pace_for_running() -> None:
    session = make_session(
        prescription={
            "version": 1,
            "blocks": [],
            "work_structure": {
                "type": "continuous",
                "continuous_minutes": 40,
            },
            "intensity": {
                "targets": [
                    {
                        "reference": "vma_percent",
                        "minimum": 80,
                        "maximum": 90,
                        "derived": {
                            "pace_seconds_per_km": {
                                "fastest": 266.67,
                                "slowest": 300,
                            }
                        },
                    }
                ]
            },
        }
    )

    payload = map_training_session_to_coros(session)
    main = payload.course["sections"][0]

    assert main["intensityType"] == 2
    assert main["intensityValueStart"] == 267
    assert main["intensityValueEnd"] == 300


def test_rejects_rpe_only_prescription_instead_of_inventing_watch_target() -> None:
    session = make_session(
        prescription={
            "version": 1,
            "blocks": [],
            "work_structure": {
                "type": "continuous",
                "continuous_minutes": 40,
            },
            "intensity": {
                "targets": [
                    {
                        "reference": "rpe",
                        "minimum": 2,
                        "maximum": 3,
                        "unit": "/10",
                    }
                ]
            },
        }
    )

    with pytest.raises(CorosWorkoutMappingError, match="uniquement exprimée en RPE"):
        map_training_session_to_coros(session)


def test_rejects_time_target_for_trail() -> None:
    session = make_session(
        sport_type="TrailRun",
        prescription=heart_rate_prescription(
            {
                "type": "continuous",
                "continuous_minutes": 45,
            },
            blocks=[
                {"name": "Échauffement", "duration_minutes": 10},
            ],
        )
    )

    with pytest.raises(CorosWorkoutMappingError, match="cible en distance"):
        map_training_session_to_coros(session)


def test_rejects_trail_intervals_with_time_based_recovery() -> None:
    session = make_session(
        sport_type="TrailRun",
        prescription=heart_rate_prescription(
            {
                "type": "repeats",
                "intervals": [
                    {
                        "repetitions": 5,
                        "work_distance_meters": 200,
                        "repetition_target": None,
                        "recovery_duration": 60,
                        "recovery_unit": "seconds",
                    }
                ],
            }
        )
    )

    with pytest.raises(CorosWorkoutMappingError, match="récupération chronométrée"):
        map_training_session_to_coros(session)


def test_rejects_strength_and_completed_sessions() -> None:
    strength = make_session(
        sport_type="Strength",
        prescription=heart_rate_prescription(
            {"type": "continuous", "continuous_minutes": 30}
        ),
    )
    completed = make_session(
        status="completed",
        prescription=heart_rate_prescription(
            {"type": "continuous", "continuous_minutes": 30}
        ),
    )

    with pytest.raises(CorosWorkoutMappingError, match="course, trail et vélo"):
        map_training_session_to_coros(strength)
    with pytest.raises(CorosWorkoutMappingError, match="planifiées"):
        map_training_session_to_coros(completed)


def test_rejects_missing_structured_prescription() -> None:
    session = make_session(prescription=None)

    with pytest.raises(CorosWorkoutMappingError, match="prescription structurée"):
        map_training_session_to_coros(session)
