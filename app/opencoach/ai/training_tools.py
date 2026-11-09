"""Outil historique d'entraînement basé sur TrainingStatsService."""
from __future__ import annotations

from datetime import date, timedelta
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from opencoach.ai.tool_engine import AITool
from opencoach.training import TrainingStatsService


class TrainingHistoryArguments(BaseModel):
    """Paramètres bornés de l'historique sportif."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    nb_days: int = Field(
        default=7,
        ge=1,
        le=365,
        description="Nombre de jours calendaires inclus dans la période.",
    )


def build_training_history_tool(
    service: TrainingStatsService,
    athlete_profile_id: UUID,
    *,
    reference_date_provider=date.today,
) -> AITool:
    """Construit l'outil pour un athlète authentifié.

    L'identifiant d'athlète et la date de référence sont injectés par OpenCoach,
    jamais choisis par le modèle.
    """

    def execute(arguments: BaseModel) -> dict:
        nb_days = arguments.nb_days
        end_date = reference_date_provider()
        start_date = end_date - timedelta(days=nb_days - 1)
        stats = service.calculate(
            athlete_profile_id,
            start_date,
            end_date,
        )
        sessions_count = stats.sessions_count

        def coverage(available: int) -> dict[str, int | str | None]:
            if sessions_count == 0:
                state = "no_sessions"
            elif available == 0:
                state = "unavailable"
            elif available < sessions_count:
                state = "partial"
            else:
                state = "complete"
            return {
                "available_sessions": available,
                "total_sessions": sessions_count,
                "status": state,
            }

        load_available = (
            stats.measured_load_data_count + stats.manual_sessions_count
        )
        return {
            "period": {
                "start_date": stats.start_date.isoformat(),
                "end_date": stats.end_date.isoformat(),
                "nb_days": nb_days,
                "inclusive": True,
            },
            "sessions": {
                "total": sessions_count,
                "coros_activities": stats.activities_count,
                "manual_completed_sessions": stats.manual_sessions_count,
            },
            "metrics": {
                "duration_minutes": {
                    "value": stats.total_duration_minutes,
                    "unit": "minutes",
                    "coverage": {
                        "status": "calculated_from_recorded_sessions",
                        "total_sessions": sessions_count,
                    },
                },
                "distance_km": {
                    "value": stats.total_distance_km,
                    "unit": "km",
                    "coverage": coverage(stats.distance_data_count),
                },
                "elevation_gain_m": {
                    "value": stats.total_elevation_gain_m,
                    "unit": "m",
                    "coverage": coverage(stats.elevation_data_count),
                },
                "training_load": {
                    "measured": stats.measured_load,
                    "estimated": stats.estimated_load,
                    "total": stats.total_load,
                    "unit": "load_points",
                    "coverage": coverage(load_available),
                },
            },
        }

    return AITool(
        name="training_history",
        description=(
            "Retourne le bilan réel des entraînements sur les nb_days derniers "
            "jours calendaires inclusifs : séances, durée, distance, D+ et charge. "
            "Les métriques précisent leur couverture de données."
        ),
        arguments_model=TrainingHistoryArguments,
        handler=execute,
    )
