"""Outil de tendances calculées par les services statistiques OpenCoach."""
from __future__ import annotations

from datetime import date, timedelta
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from opencoach.ai.tool_engine import AITool
from opencoach.training import TrainingStatsService


class TrainingTrendsArguments(BaseModel):
    """Fenêtres comparables pour l'analyse de tendance."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    nb_days: int = Field(
        ge=1,
        le=180,
        description="Durée de la période récente, en jours.",
    )
    comparison_days: int = Field(
        ge=1,
        le=180,
        description="Durée de la période précédente de comparaison, en jours.",
    )


def build_training_trends_tool(
    service: TrainingStatsService,
    athlete_profile_id: UUID,
    *,
    reference_date_provider=date.today,
) -> AITool:
    """Construit un outil de comparaison de deux périodes successives."""

    def execute(arguments: BaseModel) -> dict:
        reference_date = reference_date_provider()
        current_end = reference_date - timedelta(days=1)
        current_start = current_end - timedelta(days=arguments.nb_days - 1)
        comparison_end = current_start - timedelta(days=1)
        comparison_start = comparison_end - timedelta(
            days=arguments.comparison_days - 1
        )

        current = service.calculate(
            athlete_profile_id,
            current_start,
            current_end,
        )
        comparison = service.calculate(
            athlete_profile_id,
            comparison_start,
            comparison_end,
        )

        def metric_snapshot(
            stats,
            *,
            value: float | int,
            available: int,
            unit: str,
        ) -> dict:
            total = stats.sessions_count
            if total == 0:
                coverage_status = "no_sessions"
            elif available == 0:
                coverage_status = "unavailable"
            elif available < total:
                coverage_status = "partial"
            else:
                coverage_status = "complete"

            return {
                "value": value if coverage_status == "complete" else None,
                "partial_observed_value": (
                    value if coverage_status == "partial" else None
                ),
                "unit": unit,
                "coverage": {
                    "available_sessions": available,
                    "total_sessions": total,
                    "status": coverage_status,
                },
            }

        def trend(current_metric: dict, comparison_metric: dict) -> dict:
            current_value = current_metric["value"]
            comparison_value = comparison_metric["value"]
            if current_value is None or comparison_value is None:
                return {
                    "delta": None,
                    "percent_delta": None,
                    "status": "insufficient_coverage",
                }

            delta = round(current_value - comparison_value, 2)
            percent_delta = (
                round(delta / comparison_value * 100, 1)
                if comparison_value != 0
                else None
            )
            return {
                "delta": delta,
                "percent_delta": percent_delta,
                "status": "complete",
            }

        metric_definitions = {
            "duration_minutes": (
                "minutes",
                lambda stats: stats.duration_data_count,
                lambda stats: stats.total_duration_minutes,
            ),
            "distance_km": (
                "km",
                lambda stats: stats.distance_data_count,
                lambda stats: stats.total_distance_km,
            ),
            "elevation_gain_m": (
                "m",
                lambda stats: stats.elevation_data_count,
                lambda stats: stats.total_elevation_gain_m,
            ),
            "training_load": (
                "load_points",
                lambda stats: stats.measured_load_data_count + stats.manual_sessions_count,
                lambda stats: stats.total_load,
            ),
        }

        metrics = {}
        warnings = []
        for name, (unit, available_count, value_getter) in metric_definitions.items():
            current_metric = metric_snapshot(
                current,
                value=value_getter(current),
                available=available_count(current),
                unit=unit,
            )
            comparison_metric = metric_snapshot(
                comparison,
                value=value_getter(comparison),
                available=available_count(comparison),
                unit=unit,
            )
            metrics[name] = {
                "current_period": current_metric,
                "comparison_period": comparison_metric,
                "trend": trend(current_metric, comparison_metric),
            }
            if (
                current_metric["coverage"]["status"] != "complete"
                or comparison_metric["coverage"]["status"] != "complete"
            ):
                warnings.append(
                    f"Tendance {name} non calculée : couverture incomplète sur au moins une période."
                )

        return {
            "current_period": {
                "start_date": current.start_date.isoformat(),
                "end_date": current.end_date.isoformat(),
                "nb_days": arguments.nb_days,
                "sessions": current.sessions_count,
            },
            "comparison_period": {
                "start_date": comparison.start_date.isoformat(),
                "end_date": comparison.end_date.isoformat(),
                "nb_days": arguments.comparison_days,
                "sessions": comparison.sessions_count,
            },
            "metrics": metrics,
            "warnings": warnings,
        }

    return AITool(
        name="training_trends",
        description=(
            "Compare les tendances d'entraînement entre deux périodes successives. "
            "Les paramètres nb_days et comparison_days sont obligatoires : demande les "
            "deux durées si elles manquent et attends la réponse. Les écarts ne sont "
            "calculés que lorsque les deux périodes ont une couverture complète."
        ),
        arguments_model=TrainingTrendsArguments,
        handler=execute,
    )
