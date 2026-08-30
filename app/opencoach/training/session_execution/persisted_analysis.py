"""Résultat persistant d'une analyse d'exécution de séance."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class PersistedSessionExecutionAnalysis:
    """Débriefing sauvegardé d'une séance validée par l'athlète."""

    id: UUID

    athlete_profile_id: UUID
    training_session_id: UUID
    activity_id: UUID

    goal_type: str
    overall_status: str
    technical_status: str | None

    objective: str

    metrics: tuple[dict, ...]

    strengths: tuple[str, ...]
    attention_points: tuple[str, ...]

    debriefing: str

    derived_results: tuple[
        tuple[str, float],
        ...,
    ]

    analyzed_at: datetime
