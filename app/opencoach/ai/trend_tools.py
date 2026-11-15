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

        comparison_result = current.compare_to(comparison)

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
            "metrics": comparison_result["metrics"],
            "warnings": comparison_result["warnings"],
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
