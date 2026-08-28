from dataclasses import dataclass
from datetime import date
from uuid import UUID


@dataclass
class TrainingSession:
    """Séance d'entraînement planifiée dans OpenCoach."""

    id: UUID | None

    date: date
    type: str
    sport_type: str

    title: str
    description: str

    duration_minutes: int

    planning_key: str | None = None

    distance_km: float | None = None
    elevation_gain_m: float | None = None

    intensity: str = ""
    heart_rate_zone: str | None = None

    prescription: dict | None = None

    status: str = "planned"

    activity_id: UUID | None = None