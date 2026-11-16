from dataclasses import dataclass

from .stats import TrainingStats

from .load_comparison import (
    TrainingLoadComparison,
)


@dataclass(frozen=True)
class RecentTrainingLoad:
    """Synthèse récente des écarts entre charge prévue et charge réelle."""

    days: tuple[
        TrainingLoadComparison,
        ...,
    ]

    analyzed_days: int

    planned_load_total: float
    actual_load_total: float

    above_plan_days: int
    below_plan_days: int
    on_plan_days: int

    broken_rest_days: int
    respected_rest_days: int

    planning_covered_days: int = 0
    unplanned_days: int = 0

    @property
    def planned_sessions_count(self) -> int:
        """Nombre de séances prescrites dans la période analysée."""
        return sum(
            day.planned_sessions_count
            for day in self.days
        )

    @property
    def planning_coverage_ratio(self) -> float:
        """Part des jours couverts par une prescription OpenCoach."""

        if self.analyzed_days <= 0:
            return 0.0

        return round(
            self.planning_covered_days
            / self.analyzed_days,
            3,
        )

    @property
    def load_delta_total(self) -> float:
        """Écart cumulé entre charge réelle et charge prévue."""
        return round(
            self.actual_load_total
            - self.planned_load_total,
            2,
        )

    @property
    def load_ratio(self) -> float | None:
        """Ratio cumulé entre charge réelle et charge prévue."""

        if self.planned_load_total <= 0:
            return None

        return round(
            self.actual_load_total
            / self.planned_load_total,
            3,
        )

    @property
    def has_training_history(self) -> bool:
        """Indique si au moins un jour contient une charge réelle."""
        return any(
            day.actual_load > 0
            for day in self.days
        )

    def analysis_summary(self, stats: TrainingStats) -> dict:
        """Construit le bilan métier combinant charge planifiée et entraînement réel.

        Les règles de couverture, de fiabilité des totaux et d'interprétation
        des journées sont centralisées dans le domaine training.
        """
        actual_sessions = stats.sessions_count
        estimated_load_data_count = stats.estimated_load_data_count
        available_load_sessions = stats.measured_load_data_count + estimated_load_data_count
        load_coverage = stats.coverage(available_load_sessions)
        duration_coverage = stats.coverage(stats.duration_data_count)
        distance_coverage = stats.coverage(stats.distance_data_count)
        elevation_coverage = stats.coverage(stats.elevation_data_count)

        volume = {
            "duration_minutes": stats.total_duration_minutes if actual_sessions > 0 and stats.duration_data_count == actual_sessions else None,
            "partial_duration_minutes": stats.total_duration_minutes if 0 < stats.duration_data_count < actual_sessions else None,
            "duration_coverage": duration_coverage,
            "distance_km": stats.total_distance_km if actual_sessions > 0 and stats.distance_data_count == actual_sessions else None,
            "partial_distance_km": stats.total_distance_km if 0 < stats.distance_data_count < actual_sessions else None,
            "distance_coverage": distance_coverage,
            "elevation_gain_m": stats.total_elevation_gain_m if actual_sessions > 0 and stats.elevation_data_count == actual_sessions else None,
            "partial_elevation_gain_m": stats.total_elevation_gain_m if 0 < stats.elevation_data_count < actual_sessions else None,
            "elevation_coverage": elevation_coverage,
            "activity_count": stats.activities_count,
            "manual_session_count": stats.manual_sessions_count,
        }

        coverage_status = load_coverage["status"]
        has_complete_load = coverage_status == "complete"
        daily = [
            {
                "date": day.date.isoformat(),
                "status": day.status if has_complete_load or day.actual_sessions_count == 0 else "load_data_incomplete",
                "planned_load": day.planned_load,
                "actual_load": day.actual_load if has_complete_load and day.actual_sessions_count else None,
                "load_delta": day.load_delta if has_complete_load and day.actual_sessions_count else None,
                "planned_sessions": day.planned_sessions_count,
                "actual_sessions": day.actual_sessions_count,
            }
            for day in sorted(self.days, key=lambda item: item.date)
        ]

        warnings = []
        if self.unplanned_days:
            warnings.append(
                f"Le planning OpenCoach ne couvre pas {self.unplanned_days} jour(s) de la période."
            )
        if coverage_status == "no_sessions":
            warnings.append(
                "Aucune séance réalisée enregistrée : la charge réelle est indisponible, pas égale à zéro."
            )
        elif coverage_status == "unavailable":
            warnings.append(
                f"Aucune charge exploitable pour les {actual_sessions} séance(s) enregistrée(s)."
            )
        elif coverage_status == "partial":
            warnings.append(
                f"Charge partielle : {available_load_sessions}/{actual_sessions} séances disposent d'une charge exploitable. Le total complet est masqué."
            )

        return {
            "period": {
                "start_date": stats.start_date.isoformat(),
                "end_date": stats.end_date.isoformat(),
                "nb_days": (stats.end_date - stats.start_date).days + 1,
                "inclusive": True,
            },
            "volume": volume,
            "sessions": {
                "planned": self.planned_sessions_count,
                "actual": actual_sessions,
                "comparison_supported": False,
                "meaning": (
                    "Comptages séparés des séances planifiées et réalisées. "
                    "Ils ne prouvent pas que les séances réalisées correspondent "
                    "aux séances planifiées ; ne pas calculer de pourcentage "
                    "de réalisation ou d'adhérence à partir de ces deux nombres."
                ),
            },
            "load": {
                "planned_total": self.planned_load_total,
                "actual_total": stats.total_load if has_complete_load else None,
                "partial_observed_total": stats.total_load if coverage_status == "partial" else None,
                "measured_total": stats.measured_load if has_complete_load else None,
                "estimated_total": stats.estimated_load if has_complete_load else None,
                "delta_total": self.load_delta_total if has_complete_load else None,
                "ratio": self.load_ratio if has_complete_load else None,
                "coverage": {
                    **load_coverage,
                    "measured_sessions": stats.measured_load_data_count,
                    "estimated_manual_sessions": estimated_load_data_count,
                },
                "unit": "load_points",
            },
            "planning_coverage": {
                "covered_days": self.planning_covered_days,
                "unplanned_days": self.unplanned_days,
                "ratio": self.planning_coverage_ratio,
                "meaning": (
                    "Jours sans couverture de planning OpenCoach. Cela ne signifie "
                    "ni absence d'entraînement, ni absence d'activité importée."
                ),
            },
            "distribution": {
                "above_plan_days": self.above_plan_days,
                "on_plan_days": self.on_plan_days,
                "below_plan_days": self.below_plan_days,
                "broken_rest_days": self.broken_rest_days,
                "respected_rest_days": self.respected_rest_days,
            },
            "daily": daily,
            "warnings": warnings,
        }
