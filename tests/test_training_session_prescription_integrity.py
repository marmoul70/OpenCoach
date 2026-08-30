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
