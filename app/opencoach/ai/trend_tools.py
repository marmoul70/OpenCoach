"""Adaptateur conversationnel des tendances statistiques OpenCoach."""
from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from opencoach.coaching.capabilities.registry import CoachCapability as AITool
from opencoach.training import TrainingStatsService


class TrainingTrendsArguments(BaseModel):
    """Paramètres techniques de la demande de comparaison."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    nb_days: int = Field(
        description="Durée de la période récente, en jours.",
    )
    comparison_days: int = Field(
        description="Durée de la période précédente de comparaison, en jours.",
    )


def build_training_trends_tool(
    service: TrainingStatsService,
    athlete_profile_id: UUID,
) -> AITool:
    """Expose la comparaison calculée par le service statistique Coach."""

    def execute(arguments: BaseModel) -> dict:
        return service.compare_adjacent_periods(
            athlete_profile_id,
            current_days=arguments.nb_days,
            comparison_days=arguments.comparison_days,
        )

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
