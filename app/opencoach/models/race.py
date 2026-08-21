from dataclasses import dataclass
from datetime import date
from uuid import UUID


@dataclass
class Race:
    """Course planifiée ou réalisée par l'athlète."""

    id: UUID | None

    date: date

    name: str
    location: str

    race_type: str
    priority: str

    distance_km: float
    elevation_gain_m: float | None = None

    target_time_minutes: int | None = None

    status: str = "planned"

    actual_distance_km: float | None = None
    actual_elevation_gain_m: float | None = None
    actual_time_minutes: int | None = None

    ranking: int | None = None
    notes: str = ""

    activity_id: UUID | None = None
