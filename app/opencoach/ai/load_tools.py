"""Outil de synthèse de charge récente, basé sur les services métier existants."""
from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from opencoach.ai.tool_engine import AITool
from opencoach.training import RecentTrainingLoadService, TrainingStatsService


class TrainingLoadArguments(BaseModel):
    """Période demandée pour l'analyse de charge."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    nb_days: int = Field(
        ge=1,
        le=90,
        description="Nombre de jours calendaires précédant la date de référence.",
    )


def build_training_load_tool(
    service: RecentTrainingLoadService,
    training_stats_service: TrainingStatsService,
    athlete_profile_id: UUID,
    *,
    reference_date_provider=date.today,
) -> AITool:
    """Construit l'outil de charge pour l'athlète authentifié."""

    def execute(arguments: BaseModel) -> dict:
        nb_days = arguments.nb_days
        target_date = reference_date_provider()
        load = service.calculate(
            athlete_profile_id,
            target_date,
            days=nb_days,
        )
        stats = training_stats_service.calculate_days(
            athlete_profile_id,
            target_date,
            days=nb_days,
            include_reference_day=False,
        )

        return load.analysis_summary(stats)

    return AITool(
        name="training_load",
        description=(
            "Retourne la charge d'entraînement réelle et prévue sur les nb_days derniers "
            "jours calendaires inclusifs, avec écarts quotidiens et couverture du planning. "
            "nb_days est obligatoire : demande la période si elle manque et attends la réponse. "
            "Une charge réelle sans couverture complète n'est jamais présentée comme un total fiable. "
            "Les résultats proviennent exclusivement des services métier et des données centralisées dans OpenCoach."
        ),
        arguments_model=TrainingLoadArguments,
        handler=execute,
    )
