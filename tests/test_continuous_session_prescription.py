from opencoach.planning.sessions.prescription.continuous import (
    build_continuous_session_prescription,
)
from opencoach.planning.stimulus.training import (
    TrainingStimulus,
)


def test_aerobic_easy_without_physiology_uses_rpe() -> None:
    prescription = (
        build_continuous_session_prescription(
            stimulus=(
                TrainingStimulus.AEROBIC_EASY
            ),
            duration_minutes=45,
            physiology=None,
        )
    )

    assert prescription["version"] == 1

    structure = prescription[
        "work_structure"
    ]

    assert (
        structure["stimulus"]
        == "aerobic_easy"
    )

    assert (
        structure["type"]
        == "continuous"
    )

    assert (
        structure["available_minutes"]
        == 45
    )

    assert (
        structure["continuous_minutes"]
        == 45
    )

    targets = prescription[
        "intensity"
    ][
        "targets"
    ]

    assert targets

    assert (
        targets[0]["reference"]
        == "rpe"
    )


def test_recovery_builds_consistent_structure() -> None:
    prescription = (
        build_continuous_session_prescription(
            stimulus=(
                TrainingStimulus.RECOVERY
            ),
            duration_minutes=30,
            physiology=None,
        )
    )

    structure = prescription[
        "work_structure"
    ]

    assert (
        structure["stimulus"]
        == "recovery"
    )

    assert (
        structure["continuous_minutes"]
        == 30
    )


def test_continuous_prescription_rejects_invalid_duration() -> None:
    try:
        build_continuous_session_prescription(
            stimulus=(
                TrainingStimulus.AEROBIC_EASY
            ),
            duration_minutes=0,
            physiology=None,
        )

    except ValueError:
        return

    raise AssertionError(
        "Une durée nulle aurait dû être refusée."
    )


def test_non_continuous_stimulus_is_rejected() -> None:
    try:
        build_continuous_session_prescription(
            stimulus=(
                TrainingStimulus.VO2MAX
            ),
            duration_minutes=45,
            physiology=None,
        )

    except ValueError:
        return

    raise AssertionError(
        "VO2MAX ne doit pas être reconstruit "
        "comme une séance continue générique."
    )
