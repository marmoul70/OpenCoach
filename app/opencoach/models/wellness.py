from dataclasses import dataclass
from datetime import date, datetime


@dataclass
class WellnessDay:
    """Données quotidiennes de forme et récupération."""

    provider: str
    date: date

    fitness_ctl: float | None = None
    fatigue_atl: float | None = None
    ramp_rate: float | None = None
    steps: int | None = None

    provider_updated_at: datetime | None = None
