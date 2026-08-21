from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class TrainingStats:
    """Statistiques d'entraînement réellement effectué."""

    start_date: date
    end_date: date

    activities_count: int
    manual_sessions_count: int

    total_duration_minutes: int
    total_distance_km: float
    total_elevation_gain_m: float

    measured_load: float
    estimated_load: float

    @property
    def sessions_count(self) -> int:
        """Nombre total d'efforts réellement effectués."""
        return (
            self.activities_count
            + self.manual_sessions_count
        )

    @property
    def total_load(self) -> float:
        """Charge totale mesurée et estimée."""
        return round(
            self.measured_load
            + self.estimated_load,
            2,
        )
