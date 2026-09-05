from dataclasses import dataclass
from datetime import date, datetime
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
    planning_importance: str | None = None

    distance_km: float | None = None
    elevation_gain_m: float | None = None

    intensity: str = ""
    heart_rate_zone: str | None = None

    prescription: dict | None = None

    status: str = "planned"

    activity_id: UUID | None = None

    intervals_external_id: str | None = None

    intervals_event_id: str | None = None

    intervals_sync_status: str | None = None

    intervals_last_synced_at: datetime | None = None

    intervals_payload_hash: str | None = None

    intervals_sync_error: str | None = None