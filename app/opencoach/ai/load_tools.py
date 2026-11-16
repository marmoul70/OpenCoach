"""Outil de synthèse de charge récente, basé sur une capacité Coach unique."""
from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from opencoach.coaching.capabilities.registry import CoachCapability as AITool
from opencoach.training import RecentTrainingLoadService


class TrainingLoadArguments(BaseModel):
    """Période demandée pour l'analyse de charge."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    nb_days: int | None = Field(
        default=None,
        description="Nombre de jours calendaires précédant la date de référence. Si absent, le domaine applique sa fenêtre par défaut.",
    )


def build_training_load_tool(
    service: RecentTrainingLoadService,
    athlete_profile_id: UUID,
) -> AITool:
    """Expose la synthèse charge + volume calculée par le domaine training."""

    def execute(arguments: BaseModel) -> dict:
        period_arguments = (
            {"days": arguments.nb_days}
            if arguments.nb_days is not None
            else {}
        )
        return service.analysis_summary(
            athlete_profile_id,
            **period_arguments,
        )

    return AITool(
        name="training_load",
        description=(
            "Retourne la charge d'entraînement réelle et prévue sur la période demandée, "
            "avec écarts quotidiens et couverture du planning. "
            "nb_days est facultatif : en son absence, le domaine applique sa fenêtre par défaut. "
            "Une charge réelle sans couverture complète n'est jamais présentée comme un total fiable. "
            "Les résultats proviennent exclusivement des services métier et des données centralisées dans OpenCoach."
        ),
        arguments_model=TrainingLoadArguments,
        handler=execute,
    )
