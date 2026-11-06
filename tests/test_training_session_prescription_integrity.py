from datetime import date

import pytest

from opencoach.models import TrainingSession
from opencoach.planning.sessions.prescription.integrity import (
    TrainingSessionPrescriptionIntegrityError,
    validate_training_session_prescription,
)


def session(
    *,
    session_type: str = "aerobic_easy",
    planning_key: str | None = "2026-08-31:monday",
    prescription=None,
) -> TrainingSession:
    if prescription is None:
        prescription = {
            "version": 1,
            "blocks": [],
            "work_structure": {
                "type": "continuous",
                "stimulus": session_type,
                "available_minutes": 45,
                "continuous_minutes": 45,
                "description": "Endurance facile.",
                "circuit": None,
                "intervals": [],
            },
            "intensity": {
                "targets": [
                    {
                        "reference": "heart_rate",
                        "minimum": 129,
                        "maximum": 152,
                        "unit": "bpm",
                    },
                ],
                "guidance": [],
            },
        }

    return TrainingSession(
        id=None,
        date=date(2026, 8, 31),
        type=session_type,
        sport_type="Run",
        title="Endurance facile",
        description="Test",
        duration_minutes=45,
        planning_key=planning_key,
        intensity="easy",
        prescription=prescription,
    )


def test_valid_generated_session_is_accepted() -> None:
    validate_training_session_prescription(
        session()
    )


def test_manual_session_can_have_no_prescription() -> None:
    value = session(
        planning_key=None,
        prescription={},
    )

    value.prescription = None

    validate_training_session_prescription(
        value
    )


def test_generated_session_requires_prescription() -> None:
    value = session()
    value.prescription = None

    with pytest.raises(
        TrainingSessionPrescriptionIntegrityError
    ):
        validate_training_session_prescription(
            value
        )


def test_generated_session_rejects_stale_stimulus() -> None:
    value = session()

    assert value.prescription is not None

    value.prescription[
        "work_structure"
    ][
        "stimulus"
    ] = "vo2max"

    with pytest.raises(
        TrainingSessionPrescriptionIntegrityError
    ):
        validate_training_session_prescription(
            value
        )


def test_generated_session_requires_intensity_targets() -> None:
    value = session()

    assert value.prescription is not None

    value.prescription[
        "intensity"
    ][
        "targets"
    ] = []

    with pytest.raises(
        TrainingSessionPrescriptionIntegrityError
    ):
        validate_training_session_prescription(
            value
        )


def test_version_two_prescription_accepts_ordered_phases_and_block_targets() -> None:
    value = session(
        prescription={
            "version": 2,
            "blocks": [
                {
                    "name": "Échauffement",
                    "description": "Mise en route progressive.",
                    "duration_minutes": 10,
                    "phase": "warmup",
                    "intensity": {
                        "targets": [
                            {
                                "reference": "heart_rate",
                                "minimum": 120,
                                "maximum": 140,
                                "unit": "bpm",
                            }
                        ],
                        "guidance": [],
                    },
                },
                {
                    "name": "Bloc principal",
                    "description": "Travail au seuil.",
                    "duration_minutes": 35,
                    "phase": "main",
                    "intensity": {
                        "targets": [
                            {
                                "reference": "vma_percent",
                                "minimum": 80,
                                "maximum": 90,
                                "unit": "% VMA",
                            }
                        ],
                        "guidance": [],
                    },
                },
            ],
            "work_structure": {
                "type": "continuous",
                "stimulus": "aerobic_easy",
                "available_minutes": 40,
                "continuous_minutes": 40,
                "description": "Travail continu.",
                "circuit": None,
                "intervals": [],
            },
            "intensity": {
                "targets": [
                    {
                        "reference": "heart_rate",
                        "minimum": 140,
                        "maximum": 155,
                        "unit": "bpm",
                    }
                ],
                "guidance": [],
            },
        }
    )

    validate_training_session_prescription(value)


def test_version_two_rejects_unknown_phase() -> None:
    value = session()
    assert value.prescription is not None
    value.prescription["version"] = 2
    value.prescription["blocks"] = [
        {"name": "Bloc", "description": "Test", "phase": "unknown"}
    ]

    with pytest.raises(TrainingSessionPrescriptionIntegrityError):
        validate_training_session_prescription(value)


def test_version_two_requires_explicit_phase_name_and_description() -> None:
    value = session(
        prescription={
            "version": 2,
            "blocks": [
                {
                    "name": "Bloc",
                    "description": "Consigne.",
                    "duration_minutes": 45,
                    "intensity": {
                        "targets": [
                            {
                                "reference": "rpe",
                                "minimum": 3,
                                "maximum": 4,
                                "unit": "/10",
                            }
                        ],
                        "guidance": [],
                    },
                }
            ],
            "work_structure": {
                "type": "continuous",
                "stimulus": "aerobic_easy",
                "available_minutes": 45,
                "continuous_minutes": 45,
                "description": "Travail continu.",
                "circuit": None,
                "intervals": [],
            },
            "intensity": {
                "targets": [
                    {
                        "reference": "rpe",
                        "minimum": 3,
                        "maximum": 4,
                        "unit": "/10",
                    }
                ],
                "guidance": [],
            },
        }
    )

    with pytest.raises(
        TrainingSessionPrescriptionIntegrityError,
        match="Phase de séance absente",
    ):
        validate_training_session_prescription(value)


def test_version_two_requires_phase_durations_to_match_session_duration() -> None:
    value = session(
        prescription={
            "version": 2,
            "blocks": [
                {
                    "name": "Séance",
                    "description": "Travail continu.",
                    "duration_minutes": 40,
                    "phase": "main",
                    "intensity": {
                        "targets": [
                            {
                                "reference": "rpe",
                                "minimum": 3,
                                "maximum": 4,
                                "unit": "/10",
                            }
                        ],
                        "guidance": [],
                    },
                }
            ],
            "work_structure": {
                "type": "continuous",
                "stimulus": "aerobic_easy",
                "available_minutes": 40,
                "continuous_minutes": 40,
                "description": "Travail continu.",
                "circuit": None,
                "intervals": [],
            },
            "intensity": {
                "targets": [
                    {
                        "reference": "rpe",
                        "minimum": 3,
                        "maximum": 4,
                        "unit": "/10",
                    }
                ],
                "guidance": [],
            },
        }
    )

    with pytest.raises(
        TrainingSessionPrescriptionIntegrityError,
        match="ne correspond pas à la durée totale",
    ):
        validate_training_session_prescription(value)


def test_version_two_rejects_invalid_interval_work_and_recovery_targets() -> None:
    value = session()
    assert value.prescription is not None
    value.prescription["version"] = 2
    value.prescription["blocks"] = [
        {
            "name": "Bloc principal",
            "description": "Intervalles.",
            "duration_minutes": 45,
            "phase": "main",
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
    ]
    value.prescription["work_structure"]["intervals"] = [
        {
            "repetitions": 5,
            "work_duration": 60,
            "work_unit": "seconds",
            "work_distance_meters": 400,
            "recovery_duration": 30,
            "recovery_unit": "seconds",
        }
    ]
    value.prescription["recovery_intensity"] = {
        "targets": [
            {
                "reference": "rpe",
                "minimum": 1,
                "maximum": 2,
                "unit": "/10",
            }
        ],
        "guidance": [],
    }

    with pytest.raises(
        TrainingSessionPrescriptionIntegrityError,
        match="exactement une durée ou une distance",
    ):
        validate_training_session_prescription(value)


def test_version_two_accepts_work_and_recovery_elevation_with_time_budgets() -> None:
    intensity = {
        "targets": [
            {
                "reference": "rpe",
                "minimum": 3,
                "maximum": 4,
                "unit": "/10",
            }
        ],
        "guidance": [],
    }
    value = session(
        prescription={
            "version": 2,
            "blocks": [
                {
                    "name": "Répétitions en côte",
                    "description": "Effort régulier en montée.",
                    "duration_minutes": 45,
                    "phase": "main",
                    "intensity": intensity,
                }
            ],
            "work_structure": {
                "type": "repeats",
                "stimulus": "aerobic_easy",
                "available_minutes": 45,
                "continuous_minutes": None,
                "description": "5 montées avec récupération.",
                "circuit": None,
                "intervals": [
                    {
                        "repetitions": 5,
                        "work_duration": 90,
                        "work_unit": "seconds",
                        "work_distance_meters": None,
                        "work_elevation_gain_meters": 100,
                        "recovery_duration": 60,
                        "recovery_unit": "seconds",
                        "recovery_distance_meters": None,
                        "recovery_elevation_gain_meters": 30,
                    }
                ],
            },
            "intensity": intensity,
            "recovery_intensity": intensity,
        }
    )

    validate_training_session_prescription(value)
