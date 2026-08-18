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

    resting_hr: int | None = None
    hrv: float | None = None

    sleep_seconds: int | None = None
    sleep_score: float | None = None
    sleep_quality: int | None = None
    avg_sleeping_hr: float | None = None

    spo2: float | None = None
    steps: int | None = None

    provider_updated_at: datetime | None = None