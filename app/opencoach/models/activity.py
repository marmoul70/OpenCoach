from uuid import UUID
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Activity:
    """Activité sportive normalisée utilisée par OpenCoach."""

    provider: str
    provider_activity_id: str

    name: str
    sport_type: str
    start_at: datetime

    source: str | None = None
    source_file_name: str | None = None
    start_at_local: datetime | None = None
    device_name: str | None = None

    elapsed_time_seconds: int | None = None
    moving_time_seconds: int | None = None

    distance_m: float | None = None
    elevation_gain_m: float | None = None
    elevation_loss_m: float | None = None

    average_speed_mps: float | None = None
    max_speed_mps: float | None = None

    average_heart_rate: float | None = None
    max_heart_rate: float | None = None
    lactate_threshold_heart_rate: int | None = None
    athlete_max_heart_rate: int | None = None

    average_cadence: float | None = None
    average_stride_m: float | None = None
    average_stance_time_ms: float | None = None
    average_vertical_oscillation_mm: float | None = None
    average_power_w: float | None = None

    average_altitude_m: float | None = None
    min_altitude_m: float | None = None
    max_altitude_m: float | None = None

    average_temperature_c: float | None = None
    min_temperature_c: float | None = None
    max_temperature_c: float | None = None

    calories: int | None = None

    training_load: float | None = None
    fitness_ctl: float | None = None
    fatigue_atl: float | None = None
    hr_load: float | None = None
    intensity: float | None = None
    feel: int | None = None

    id: UUID | None = None