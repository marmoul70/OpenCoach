from datetime import date

import pytest

from opencoach.models import TrainingSession
from opencoach.training.session_execution import (
    parse_structured_session_prescription,
)


def create_session(
    prescription: dict | None,
) -> TrainingSession:
    return TrainingSession(
        id=None,
        date=date(2026, 9, 1),
        type="speed_development",
        sport_type="Run",
        title="Développement de la vitesse",
        description="Test.",
        duration_minutes=30,
        intensity="hard",
        prescription=prescription,
    )


def real_speed_prescription() -> dict:
    return {
        "version": 1,
        "work_structure": {
            "type": "repeats",
            "stimulus": "speed_development",
            "available_minutes": 15,
            "continuous_minutes": None,
            "description": (
                "8 × 100 m / récupération 45 s."
            ),
            "circuit": None,
            "intervals": [
                {
                    "repetitions": 8,
                    "work_duration": None,
                    "work_unit": None,
                    "work_distance_meters": 100,
                    "repetition_target": {
                        "distance_meters": 100,
                        "vma_kmh": 15.0,
                        "vma_percent_min": 100,
                        "vma_percent_max": 115,
                        "fast_seconds": (
                            20.869565217391305
                        ),
                        "slow_seconds": 24.0,
                    },
                    "recovery_duration": 45,
                    "recovery_unit": "seconds",
                },
            ],
        },
    }


def test_parse_real_8x100_prescription() -> None:
    result = (
        parse_structured_session_prescription(
            create_session(
                real_speed_prescription()
            )
        )
    )

    assert result is not None

    assert (
        result.structure_type
        == "repeats"
    )

    assert (
        result.stimulus
        == "speed_development"
    )

    assert result.total_repetitions == 8
    assert len(result.interval_sets) == 1

    interval_set = result.interval_sets[0]

    assert interval_set.repetitions == 8
    assert interval_set.work_distance_m == 100.0

    assert (
        interval_set.work_duration_seconds
        is None
    )

    assert (
        interval_set.recovery_duration_seconds
        == 45.0
    )


def test_parse_real_repetition_target() -> None:
    result = (
        parse_structured_session_prescription(
            create_session(
                real_speed_prescription()
            )
        )
    )

    assert result is not None

    target = (
        result.interval_sets[0]
        .repetition_target
    )

    assert target is not None

    assert target.distance_m == 100.0

    assert (
        target.target_duration_min_seconds
        == pytest.approx(
            20.869565217391305
        )
    )

    assert (
        target.target_duration_max_seconds
        == 24.0
    )

    assert target.vma_kmh == 15.0
    assert target.vma_percent_min == 100.0
    assert target.vma_percent_max == 115.0


def test_duration_based_intervals_are_supported() -> None:
    prescription = {
        "work_structure": {
            "type": "repeats",
            "stimulus": "threshold",
            "intervals": [
                {
                    "repetitions": 3,
                    "work_duration": 5,
                    "work_unit": "minutes",
                    "work_distance_meters": None,
                    "recovery_duration": 2,
                    "recovery_unit": "minutes",
                    "repetition_target": None,
                },
            ],
        },
    }

    result = (
        parse_structured_session_prescription(
            create_session(
                prescription
            )
        )
    )

    assert result is not None

    interval_set = result.interval_sets[0]

    assert (
        interval_set.work_duration_seconds
        == 300.0
    )

    assert (
        interval_set.recovery_duration_seconds
        == 120.0
    )


def test_multiple_interval_sets_are_supported() -> None:
    prescription = real_speed_prescription()

    prescription[
        "work_structure"
    ]["intervals"].append(
        {
            "repetitions": 4,
            "work_duration": 30,
            "work_unit": "seconds",
            "work_distance_meters": None,
            "recovery_duration": 60,
            "recovery_unit": "seconds",
            "repetition_target": None,
        }
    )

    result = (
        parse_structured_session_prescription(
            create_session(
                prescription
            )
        )
    )

    assert result is not None
    assert len(result.interval_sets) == 2

    assert result.total_repetitions == 12


def test_session_without_work_structure_returns_none() -> None:
    result = (
        parse_structured_session_prescription(
            create_session(
                {
                    "version": 1,
                }
            )
        )
    )

    assert result is None


def test_empty_intervals_returns_none() -> None:
    result = (
        parse_structured_session_prescription(
            create_session(
                {
                    "work_structure": {
                        "type": "repeats",
                        "intervals": [],
                    },
                }
            )
        )
    )

    assert result is None


def test_interval_requires_distance_or_duration() -> None:
    prescription = {
        "work_structure": {
            "type": "repeats",
            "intervals": [
                {
                    "repetitions": 8,
                    "work_duration": None,
                    "work_unit": None,
                    "work_distance_meters": None,
                    "recovery_duration": 45,
                    "recovery_unit": "seconds",
                },
            ],
        },
    }

    with pytest.raises(
        ValueError,
        match="distance ou par durée",
    ):
        parse_structured_session_prescription(
            create_session(
                prescription
            )
        )


def test_invalid_recovery_unit_is_rejected() -> None:
    prescription = real_speed_prescription()

    prescription[
        "work_structure"
    ]["intervals"][0][
        "recovery_unit"
    ] = "hours"

    with pytest.raises(
        ValueError,
        match="non supportée",
    ):
        parse_structured_session_prescription(
            create_session(
                prescription
            )
        )


def test_invalid_repetition_count_is_rejected() -> None:
    prescription = real_speed_prescription()

    prescription[
        "work_structure"
    ]["intervals"][0][
        "repetitions"
    ] = 0

    with pytest.raises(
        ValueError,
        match="entier positif",
    ):
        parse_structured_session_prescription(
            create_session(
                prescription
            )
        )
