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

    # Nombre de séances disposant réellement de chaque métrique.
    # Les valeurs par défaut préservent la compatibilité des constructions historiques.
    duration_data_count: int = 0
    distance_data_count: int = 0
    elevation_data_count: int = 0
    measured_load_data_count: int = 0
    estimated_load_data_count: int = 0

    @property
    def sessions_count(self) -> int:
        """Nombre total d'efforts réellement effectués."""
        return (
            self.activities_count
            + self.manual_sessions_count
        )

    def coverage(self, available_sessions: int) -> dict[str, int | str]:
        """Retourne le statut canonique de couverture d'une métrique."""
        total_sessions = self.sessions_count
        if available_sessions < 0 or available_sessions > total_sessions:
            raise ValueError(
                "Le nombre de séances couvertes doit être compris entre zéro "
                "et le nombre total de séances."
            )
        if total_sessions == 0:
            status = "no_sessions"
        elif available_sessions == 0:
            status = "unavailable"
        elif available_sessions < total_sessions:
            status = "partial"
        else:
            status = "complete"
        return {
            "available_sessions": available_sessions,
            "total_sessions": total_sessions,
            "status": status,
        }

    @property
    def total_load(self) -> float:
        """Charge totale mesurée et estimée."""
        return round(
            self.measured_load
            + self.estimated_load,
            2,
        )
