from datetime import date
from uuid import uuid4

import pytest

from opencoach.integrations.intervals.workout_mapper import (
    build_intervals_external_id,
    map_training_session_to_intervals,
)
from opencoach.models import TrainingSession


def make_session(
    *,
    prescription=None,
    sport_type="Run",
    heart_rate_zone=None,
) -> TrainingSession:
    return TrainingSession(
        id=uuid4(),
        date=date(2026, 9, 8),
        type="aerobic_easy",
        sport_type=sport_type,
        title="Séance OpenCoach",
        description="Consignes coach.",
        duration_minutes=45,
        intensity="easy",
        heart_rate_zone=heart_rate_zone,
        prescription=prescription,
    )


def test_external_id_is_stable_and_uses_session_id():
    session = make_session()

    assert build_intervals_external_id(session) == (
        f"opencoach:session:{session.id}"
    )


def test_unpersisted_session_cannot_be_synced():
    session = make_session()
    session.id = None

    with pytest.raises(ValueError):
        build_intervals_external_id(session)


def test_continuous_hr_session():
    session = make_session(
        prescription={
            "version": 1,
            "work_structure": {
                "type": "continuous",
                "stimulus": "aerobic_easy",
                "available_minutes": 45,
                "continuous_minutes": 45,
            },
            "intensity": {
                "targets": [
                    {
                        "reference": "heart_rate",
                        "minimum": 129,
                        "maximum": 152,
                    },
                ],
            },
        },
    )

    payload = map_training_session_to_intervals(
        session
    )

    assert payload is not None
    assert payload.category == "WORKOUT"
    assert payload.type == "Run"
    assert payload.start_date_local == (
        "2026-09-08T00:00:00"
    )
    assert "- 45m 129-152bpm HR" in (
        payload.description
    )


def test_distance_repeats_use_individualized_pace():
    session = make_session(
        prescription={
            "version": 1,
            "work_structure": {
                "type": "repeats",
                "stimulus": "speed_development",
                "intervals": [
                    {
                        "repetitions": 4,
                        "work_duration": None,
                        "work_unit": None,
                        "work_distance_meters": 100,
                        "repetition_target": {
                            "distance_meters": 100,
                            "vma_kmh": 15.0,
                            "vma_percent_min": 100,
                            "vma_percent_max": 115,
                            "fast_seconds": 20.0,
                            "slow_seconds": 24.0,
                        },
                        "recovery_duration": 45,
                        "recovery_unit": "seconds",
                    },
                ],
            },
        },
    )

    payload = map_training_session_to_intervals(
        session
    )

    assert payload is not None

    assert "4x" in payload.description
    assert (
        "- 100mtr 3:20/km-4:00/km Pace"
        in payload.description
    )
    assert "- 45s recovery" in payload.description


def test_legacy_continuous_session_uses_hr_fallback():
    session = make_session(
        prescription=None,
        heart_rate_zone=(
            "Fréquence cardiaque individualisée: "
            "129–152 bpm"
        ),
    )

    payload = map_training_session_to_intervals(
        session
    )

    assert payload is not None
    assert "- 45m 129-152bpm HR" in (
        payload.description
    )


def test_trail_run_is_sent_as_run():
    session = make_session(
        sport_type="TrailRun",
    )

    payload = map_training_session_to_intervals(
        session
    )

    assert payload is not None
    assert payload.type == "Run"


def test_strength_is_not_exported():
    session = make_session(
        sport_type="Strength",
    )

    assert (
        map_training_session_to_intervals(
            session
        )
        is None
    )


def test_payload_hash_changes_when_workout_changes():
    first = make_session(
        prescription=None,
    )

    second = TrainingSession(
        id=first.id,
        date=first.date,
        type=first.type,
        sport_type=first.sport_type,
        title=first.title,
        description=first.description,
        duration_minutes=35,
        intensity=first.intensity,
        prescription=None,
    )

    first_payload = (
        map_training_session_to_intervals(first)
    )
    second_payload = (
        map_training_session_to_intervals(second)
    )

    assert first_payload is not None
    assert second_payload is not None

    assert (
        first_payload.external_id
        == second_payload.external_id
    )

    assert (
        first_payload.payload_hash()
        != second_payload.payload_hash()
    )
