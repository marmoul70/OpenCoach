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
                            "vma_percent_min": 95,
                            "vma_percent_max": 100,
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
    assert group["repeats"] == 5
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
    assert payload.course["sections"][1] == {
        "sectionType": 2,
        "targetType": 1,
        "targetValue": 400,
        "intensityType": 2,
        "intensityValueStart": 225,
        "intensityValueEnd": 240,
    }
    description = payload.course["courseDescription"]
    assert "Série 1 : 400 m en 1:30–1:36" in description
    assert "3:45–4:00/km" in description
    assert "95–100 % VMA" in description


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


def test_uses_run_workout_for_timed_trail_session() -> None:
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

    payload = map_training_session_to_coros(session)

    assert payload.course["sportType"] == 1
    assert payload.course["sections"][0]["targetType"] == 2
    assert "mode Trail Run" in payload.course["courseDescription"]


def test_uses_run_workout_for_trail_intervals_with_timed_recovery() -> None:
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

    payload = map_training_session_to_coros(session)

    assert payload.course["sportType"] == 1
    assert payload.course["sections"][0]["intervalGroup"] is True
    assert payload.course["sections"][0]["sets"][1]["targetType"] == 2
    assert payload.course["sections"][0]["sets"][1]["targetValue"] == 60
    assert "mode Trail Run" in payload.course["courseDescription"]


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



def test_maps_continuous_trail_session_to_climb_target_when_available() -> None:
    session = make_session(
        sport_type="TrailRun",
        prescription=heart_rate_prescription(
            {
                "type": "continuous",
                "continuous_minutes": 90,
            }
        ),
    )
    session.elevation_gain_m = 800

    payload = map_training_session_to_coros(session)

    assert payload.course["sportType"] == 5
    assert payload.course["sections"][0]["targetType"] == 3
    assert payload.course["sections"][0]["targetValue"] == 800



def test_rejects_heart_rate_reserve_when_no_absolute_bpm_target_exists() -> None:
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
                        "reference": "heart_rate_reserve",
                        "minimum": 60,
                        "maximum": 70,
                        "unit": "%",
                    },
                    {
                        "reference": "rpe",
                        "minimum": 3,
                        "maximum": 4,
                        "unit": "/10",
                    },
                ]
            },
        },
    )

    with pytest.raises(CorosWorkoutMappingError, match="uniquement exprimée en RPE"):
        map_training_session_to_coros(session)


def test_maps_easy_complement_as_a_distinct_watch_phase() -> None:
    session = make_session(
        prescription=heart_rate_prescription(
            {
                "type": "continuous",
                "available_minutes": 25,
                "continuous_minutes": 25,
                "intervals": [],
            },
            blocks=[
                {"name": "Échauffement", "phase": "warmup", "duration_minutes": 10,
                 "description": "Mise en route progressive."},
                {"name": "Bloc principal", "phase": "main", "duration_minutes": 25,
                 "description": "Endurance aérobie."},
                {"name": "Complément facile", "phase": "easy", "duration_minutes": 5,
                 "description": "Finir sans ajouter d'intensité."},
                {"name": "Retour au calme", "phase": "cooldown", "duration_minutes": 10,
                 "description": "Relâcher progressivement."},
            ],
        )
    )

    payload = map_training_session_to_coros(session)

    assert [section["sectionType"] for section in payload.course["sections"]] == [
        1, 2, 2, 4
    ]
    assert payload.course["sections"][2] == {
        "sectionType": 2,
        "targetType": 2,
        "targetValue": 300,
    }
    description = payload.course["courseDescription"]
    assert "Mise en route progressive" in description
    assert "Finir sans ajouter d'intensité" in description
    assert "Relâcher progressivement" in description


def test_maps_explicit_running_distance_target_instead_of_time() -> None:
    session = make_session(
        prescription=heart_rate_prescription(
            {
                "type": "continuous",
                "work_distance_meters": 10000,
                "continuous_minutes": 60,
            }
        )
    )

    payload = map_training_session_to_coros(session)

    assert payload.course["sections"][0]["targetType"] == 1
    assert payload.course["sections"][0]["targetValue"] == 10000


def test_maps_trail_warmup_when_an_explicit_distance_is_available() -> None:
    session = make_session(
        sport_type="TrailRun",
        prescription=heart_rate_prescription(
            {
                "type": "continuous",
                "work_distance_meters": 8000,
                "continuous_minutes": 90,
            },
            blocks=[
                {
                    "name": "Échauffement",
                    "phase": "warmup",
                    "duration_minutes": 10,
                    "target_distance_meters": 1200,
                }
            ],
        )
    )

    payload = map_training_session_to_coros(session)

    assert payload.course["sections"][0] == {
        "sectionType": 1,
        "targetType": 1,
        "targetValue": 1200,
    }


def test_splits_more_than_twenty_repetitions_without_losing_recovery_count() -> None:
    session = make_session(
        prescription=heart_rate_prescription(
            {
                "type": "repeats",
                "available_minutes": 50,
                "intervals": [
                    {
                        "repetitions": 25,
                        "work_distance_meters": 200,
                        "work_duration": None,
                        "work_unit": None,
                        "repetition_target": None,
                        "recovery_duration": 60,
                        "recovery_unit": "seconds",
                    }
                ],
            }
        )
    )

    sections = map_training_session_to_coros(session).course["sections"]

    assert [section.get("repeats") for section in sections if section.get("intervalGroup")] == [
        19, 4
    ]
    # 19 récupérations dans le premier groupe, une entre les groupes,
    # puis 4 dans le second : exactement 24 pour 25 répétitions.
    grouped_recoveries = sum(
        section["repeats"]
        for section in sections
        if section.get("intervalGroup")
    )
    between_group_recoveries = sum(
        1
        for section in sections
        if section.get("sectionType") == 3
    )
    assert grouped_recoveries + between_group_recoveries == 24


def test_maps_explicit_trail_elevation_target_from_main_phase() -> None:
    session = make_session(
        sport_type="TrailRun",
        prescription=heart_rate_prescription(
            {
                "type": "continuous",
                "continuous_minutes": 90,
            },
            blocks=[
                {
                    "name": "Travail en montée",
                    "phase": "main",
                    "duration_minutes": 90,
                    "target_elevation_gain_meters": 700,
                    "description": "Montées régulières à effort maîtrisé.",
                }
            ],
        )
    )

    payload = map_training_session_to_coros(session)

    assert payload.course["sections"][0]["targetType"] == 3
    assert payload.course["sections"][0]["targetValue"] == 700
    assert "700 m D+" in payload.course["courseDescription"]


def test_maps_distance_only_phase_without_inventing_a_duration() -> None:
    session = make_session(
        prescription=heart_rate_prescription(
            {
                "type": "continuous",
                "work_distance_meters": 8000,
            },
            blocks=[
                {
                    "name": "Échauffement",
                    "phase": "warmup",
                    "target_distance_meters": 1500,
                    "description": "Progressif.",
                }
            ],
        )
    )

    payload = map_training_session_to_coros(session)

    assert payload.course["sections"][0] == {
        "sectionType": 1,
        "targetType": 1,
        "targetValue": 1500,
    }


def test_maps_trail_repetitions_and_recovery_with_explicit_elevation_targets() -> None:
    session = make_session(
        sport_type="TrailRun",
        prescription=heart_rate_prescription(
            {
                "type": "repeats",
                "intervals": [
                    {
                        "repetitions": 5,
                        "work_elevation_gain_meters": 100,
                        "work_distance_meters": None,
                        "work_duration": 90,
                        "work_unit": "seconds",
                        "recovery_elevation_gain_meters": 30,
                        "recovery_distance_meters": None,
                        "recovery_duration": 60,
                        "recovery_unit": "seconds",
                        "repetition_target": None,
                    }
                ],
            }
        )
    )

    sections = map_training_session_to_coros(session).course["sections"]

    assert sections[0]["intervalGroup"] is True
    assert sections[0]["repeats"] == 4
    assert sections[0]["sets"] == [
        {"sectionType": 2, "targetType": 3, "targetValue": 100,
         "intensityType": 1, "intensityValueStart": 140, "intensityValueEnd": 155},
        {"sectionType": 3, "targetType": 3, "targetValue": 30},
    ]
    assert sections[1]["targetType"] == 3
    assert sections[1]["targetValue"] == 100
    description = map_training_session_to_coros(session).course["courseDescription"]
    assert "100 m D+" in description
    assert "90 seconds" in description
    assert "60 seconds" in description
    assert "30 m D+" in description


def test_maps_easy_intensity_on_recovery_sections() -> None:
    prescription = heart_rate_prescription(
        {
            "type": "repeats",
            "intervals": [
                {
                    "repetitions": 4,
                    "work_distance_meters": 400,
                    "recovery_duration": 90,
                    "recovery_unit": "seconds",
                    "repetition_target": None,
                }
            ],
        }
    )
    prescription["recovery_intensity"] = {
        "targets": [
            {
                "reference": "heart_rate",
                "minimum": 120,
                "maximum": 135,
                "unit": "bpm",
            }
        ],
        "guidance": ["Récupération active très facile."],
    }
    session = make_session(prescription=prescription)

    sections = map_training_session_to_coros(session).course["sections"]

    recovery = sections[0]["sets"][1]
    assert recovery == {
        "sectionType": 3,
        "targetType": 2,
        "targetValue": 90,
        "intensityType": 1,
        "intensityValueStart": 120,
        "intensityValueEnd": 135,
    }


def test_maps_distance_only_main_block_without_requiring_duration() -> None:
    session = make_session(
        prescription=heart_rate_prescription(
            {
                "type": "continuous",
                "continuous_minutes": None,
            },
            blocks=[
                {
                    "name": "Sortie principale",
                    "phase": "main",
                    "duration_minutes": None,
                    "target_distance_meters": 12000,
                    "description": "Endurance aérobie.",
                }
            ],
        )
    )

    payload = map_training_session_to_coros(session)

    assert payload.course["sections"][0]["targetType"] == 1
    assert payload.course["sections"][0]["targetValue"] == 12000


def test_uses_compatible_session_target_when_main_block_only_has_rpe() -> None:
    prescription = heart_rate_prescription(
        {
            "type": "continuous",
            "continuous_minutes": 30,
        },
        blocks=[
            {
                "name": "Bloc principal",
                "phase": "main",
                "duration_minutes": 30,
                "intensity": {
                    "targets": [
                        {
                            "reference": "rpe",
                            "minimum": 7,
                            "maximum": 8,
                            "unit": "/10",
                        }
                    ],
                    "guidance": [],
                },
            }
        ],
    )
    session = make_session(prescription=prescription)

    payload = map_training_session_to_coros(session)

    assert payload.course["sections"][0]["intensityType"] == 1
    assert payload.course["sections"][0]["intensityValueStart"] == 140
    assert payload.course["sections"][0]["intensityValueEnd"] == 155


def test_uses_explicit_recovery_phase_intensity_for_interval_recoveries() -> None:
    prescription = heart_rate_prescription(
        {
            "type": "repeats",
            "intervals": [
                {
                    "repetitions": 4,
                    "work_distance_meters": 400,
                    "recovery_duration": 90,
                    "recovery_unit": "seconds",
                    "repetition_target": None,
                }
            ],
        },
        blocks=[
            {
                "phase": "recovery",
                "name": "Récupération entre répétitions",
                "intensity": {
                    "targets": [
                        {
                            "reference": "heart_rate",
                            "minimum": 118,
                            "maximum": 132,
                            "unit": "bpm",
                        }
                    ],
                    "guidance": ["Rester très facile pendant la récupération."],
                },
            }
        ],
    )
    session = make_session(prescription=prescription)

    sections = map_training_session_to_coros(session).course["sections"]

    recovery = sections[0]["sets"][1]
    assert recovery == {
        "sectionType": 3,
        "targetType": 2,
        "targetValue": 90,
        "intensityType": 1,
        "intensityValueStart": 118,
        "intensityValueEnd": 132,
    }



def test_explicit_recovery_phase_overrides_legacy_global_recovery_intensity() -> None:
    prescription = heart_rate_prescription(
        {
            "type": "repeats",
            "intervals": [
                {
                    "repetitions": 4,
                    "work_distance_meters": 400,
                    "recovery_duration": 90,
                    "recovery_unit": "seconds",
                    "repetition_target": None,
                }
            ],
        },
        blocks=[
            {
                "phase": "recovery",
                "name": "Récupération prescrite",
                "intensity": {
                    "targets": [
                        {
                            "reference": "heart_rate",
                            "minimum": 118,
                            "maximum": 132,
                            "unit": "bpm",
                        }
                    ],
                    "guidance": ["Récupération très facile."],
                },
            }
        ],
    )
    prescription["recovery_intensity"] = {
        "targets": [
            {
                "reference": "heart_rate",
                "minimum": 130,
                "maximum": 145,
                "unit": "bpm",
            }
        ],
        "guidance": ["Ancienne cible globale."],
    }
    session = make_session(prescription=prescription)

    sections = map_training_session_to_coros(session).course["sections"]
    recovery = sections[0]["sets"][1]

    assert recovery["intensityType"] == 1
    assert recovery["intensityValueStart"] == 118
    assert recovery["intensityValueEnd"] == 132
