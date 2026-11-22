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
    avg_hr: float | None = None
    min_hr: float | None = None
    max_hr: float | None = None
    hrv: float | None = None
    hrv_baseline: float | None = None
    stress_avg: float | None = None

    sleep_seconds: int | None = None
    sleep_score: float | None = None
    sleep_quality: int | None = None
    sleep_deep_seconds: int | None = None
    sleep_light_seconds: int | None = None
    sleep_rem_seconds: int | None = None
    sleep_awake_seconds: int | None = None
    avg_sleeping_hr: float | None = None
    min_sleeping_hr: float | None = None
    max_sleeping_hr: float | None = None

    spo2: float | None = None
    steps: int | None = None

    provider_updated_at: datetime | None = None
    stored_at: datetime | None = None