"""Schémas HTTP de génération hebdomadaire du coach OpenCoach."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class GenerateTrainingWeekRequest(
    BaseModel
):
    """Options de génération d'une semaine."""

    model_config = ConfigDict(
        extra="forbid"
    )

    trajectory_start_date: date | None = None

    additional_context: list[
        str
    ] = Field(
        default_factory=list
    )


class GeneratedTrainingSessionResponse(
    BaseModel
):
    """Résumé d'une séance persistée."""

    id: UUID

    planning_key: str | None

    date: date

    type: str

    sport_type: str

    title: str

    description: str

    duration_minutes: int

    intensity: str

    heart_rate_zone: str | None

    status: str


class GenerateTrainingWeekResponse(
    BaseModel
):
    """Réponse du pipeline hebdomadaire complet."""

    week_start: date

    week_end: date

    phase: str

    target_load: float | None

    session_count: int

    sessions: list[
        GeneratedTrainingSessionResponse
    ]
