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

    def compare_to(self, previous: TrainingStats) -> dict[str, dict]:
        """Compare deux périodes avec les mêmes règles de couverture."""
        definitions = {
            "duration_minutes": (
                "minutes",
                self.duration_data_count,
                previous.duration_data_count,
                self.total_duration_minutes,
                previous.total_duration_minutes,
            ),
            "distance_km": (
                "km",
                self.distance_data_count,
                previous.distance_data_count,
                self.total_distance_km,
                previous.total_distance_km,
            ),
            "elevation_gain_m": (
                "m",
                self.elevation_data_count,
                previous.elevation_data_count,
                self.total_elevation_gain_m,
                previous.total_elevation_gain_m,
            ),
            "training_load": (
                "load_points",
                self.measured_load_data_count + self.estimated_load_data_count,
                previous.measured_load_data_count + previous.estimated_load_data_count,
                self.total_load,
                previous.total_load,
            ),
        }

        metrics = {}
        warnings = []
        for name, (unit, current_count, previous_count, current_value, previous_value) in definitions.items():
            current_coverage = self.coverage(current_count)
            previous_coverage = previous.coverage(previous_count)
            current_reliable = current_value if current_coverage["status"] == "complete" else None
            previous_reliable = previous_value if previous_coverage["status"] == "complete" else None

            current_metric = {
                "value": current_reliable,
                "partial_observed_value": (
                    current_value if current_coverage["status"] == "partial" else None
                ),
                "unit": unit,
                "coverage": current_coverage,
            }
            previous_metric = {
                "value": previous_reliable,
                "partial_observed_value": (
                    previous_value if previous_coverage["status"] == "partial" else None
                ),
                "unit": unit,
                "coverage": previous_coverage,
            }

            if current_reliable is None or previous_reliable is None:
                trend = {
                    "delta": None,
                    "percent_delta": None,
                    "status": "insufficient_coverage",
                }
                warnings.append(
                    f"Tendance {name} non calculée : couverture incomplète sur au moins une période."
                )
            else:
                delta = round(current_reliable - previous_reliable, 2)
                trend = {
                    "delta": delta,
                    "percent_delta": (
                        round(delta / previous_reliable * 100, 1)
                        if previous_reliable != 0 else None
                    ),
                    "status": "complete",
                }

            metrics[name] = {
                "current_period": current_metric,
                "comparison_period": previous_metric,
                "trend": trend,
            }

        return {"metrics": metrics, "warnings": warnings}

    @property
    def total_load(self) -> float:
        """Charge totale mesurée et estimée."""
        return round(
            self.measured_load
            + self.estimated_load,
            2,
        )
