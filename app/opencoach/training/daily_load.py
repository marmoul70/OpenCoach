from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class DailyTrainingLoad:
    """Synthèse de l'entraînement réellement effectué sur une journée."""

    date: date

    activities_count: int
    manual_sessions_count: int

    total_duration_minutes: int
    total_distance_km: float
    total_elevation_gain_m: float

    measured_load: float
    estimated_load: float

    sport_types: tuple[str, ...]

    @property
    def sessions_count(self) -> int:
        """Nombre total de réalisations sportives comptabilisées."""
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

    @property
    def has_training(self) -> bool:
        """Indique si une activité sportive a réellement été effectuée."""
        return self.sessions_count > 0