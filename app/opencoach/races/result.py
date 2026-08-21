from dataclasses import dataclass
from typing import Literal
from uuid import UUID


RaceResultSource = Literal[
    "activity",
    "manual",
    "none",
]


@dataclass(frozen=True)
class RaceActualResult:
    """Résultat réel retenu par OpenCoach pour une course."""

    source: RaceResultSource

    activity_id: UUID | None

    distance_km: float | None
    elevation_gain_m: float | None
    duration_minutes: float | None

    training_load: float | None
