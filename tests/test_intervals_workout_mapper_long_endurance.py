"""Contrat Intervals d'une sortie longue OpenCoach."""

from datetime import date
from uuid import uuid4

from opencoach.integrations.intervals.workout_mapper import (
    map_training_session_to_intervals,
)
from opencoach.models import TrainingSession


def test_long_endurance_contains_full_workout() -> None:
    session = TrainingSession(
        id=uuid4(),
        date=date(2026, 9, 6),
        type="long_endurance",
        sport_type="TrailRun",
        title="Sortie longue",
        description="Test",
        duration_minutes=60,
        intensity="easy",
        status="planned",
    )

    payload = map_training_session_to_intervals(
        session
    )

    assert payload is not None

    assert payload.description == (
        "Sortie longue\n"
        "\n"
        "Échauffement\n"
        "- 15m\n"
        "\n"
        "Sortie longue\n"
        "- 60m\n"
        "\n"
        "Retour au calme\n"
        "- 5m"
    )


def test_long_endurance_payload_hash_is_stable() -> None:
    session = TrainingSession(
        id=uuid4(),
        date=date(2026, 9, 6),
        type="long_endurance",
        sport_type="TrailRun",
        title="Sortie longue",
        description="Test",
        duration_minutes=60,
        intensity="easy",
        status="planned",
    )

    first = map_training_session_to_intervals(
        session
    )

    second = map_training_session_to_intervals(
        session
    )

    assert first is not None
    assert second is not None

    assert (
        first.payload_hash()
        == second.payload_hash()
    )
