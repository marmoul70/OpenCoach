from datetime import date

from pydantic import BaseModel


class TrainingStatsResponse(BaseModel):
    """Statistiques d'entraînement réellement effectué."""

    start_date: date
    end_date: date

    activities_count: int
    manual_sessions_count: int
    sessions_count: int

    total_duration_minutes: int
    total_distance_km: float
    total_elevation_gain_m: float

    measured_load: float
    estimated_load: float
    total_load: float
