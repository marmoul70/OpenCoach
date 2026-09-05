from __future__ import annotations

from datetime import date
from pathlib import Path
from uuid import uuid4

from opencoach.models import TrainingSession


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (
        ROOT
        / path
    ).read_text(
        encoding="utf-8"
    )


def test_training_session_defaults_to_no_importance() -> None:
    session = TrainingSession(
        id=uuid4(),
        date=date(2026, 9, 7),
        type="aerobic_easy",
        sport_type="Run",
        title="Endurance facile",
        description="",
        duration_minutes=45,
        intensity="easy",
    )

    assert session.planning_importance is None


def test_generated_session_carries_importance() -> None:
    source = _read(
        "app/opencoach/coaching/generation/models.py"
    )

    assert (
        "planning_importance: str | None = None"
        in source
    )


def test_generation_uses_slot_intent_importance() -> None:
    source = _read(
        "app/opencoach/coaching/generation/service.py"
    )

    assert (
        "slot.intent.importance.value"
        in source
    )


def test_mapper_preserves_generated_importance() -> None:
    source = _read(
        "app/opencoach/coaching/generation/mapper.py"
    )

    assert (
        "generated.planning_importance"
        in source
    )


def test_sql_model_persists_importance() -> None:
    from opencoach.database.models.training_session import (
        TrainingSession as TrainingSessionModel,
    )

    column = (
        TrainingSessionModel
        .__table__
        .c
        .planning_importance
    )

    assert column.nullable is True
    assert column.type.length == 20


def test_sql_repository_roundtrip_mapping_exists() -> None:
    source = _read(
        "app/opencoach/database/repositories/"
        "sql_training_session.py"
    )

    assert (
        "database_session.planning_importance"
        in source
    )

    assert (
        "session.planning_importance"
        in source
    )


def test_validation_mapping_preserves_importance() -> None:
    source = _read(
        "app/opencoach/database/repositories/"
        "sql_training_session_validation.py"
    )

    assert (
        "model.planning_importance"
        in source
    )


def test_reconstruction_paths_preserve_importance() -> None:
    paths = (
        (
            "app/opencoach/coaching/"
            "daily_session_replanning_application.py"
        ),
        (
            "app/opencoach/coaching/"
            "daily_session_rescheduling_application.py"
        ),
        (
            "app/opencoach/physiology/"
            "testing/application.py"
        ),
    )

    for path in paths:
        assert (
            "planning_importance="
            in _read(path)
        )
