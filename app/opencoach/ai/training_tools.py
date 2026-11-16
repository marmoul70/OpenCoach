"""Adaptateur conversationnel de l'historique d'entraînement."""
from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from opencoach.ai.tool_engine import AITool
from opencoach.training import TrainingStatsService


class TrainingHistoryArguments(BaseModel):
    """Paramètres de transport de la demande d'historique."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    nb_days: int | None = Field(
        default=None,
        description="Nombre de jours calendaires inclus dans la période. Si absent, le domaine applique sa fenêtre par défaut.",
    )
    exclude_current_day: bool = Field(
        default=False,
        description=(
            "Si vrai, termine la période à la veille de la date de référence "
            "pour comparer des journées entièrement écoulées."
        ),
    )


def build_training_history_tool(
    service: TrainingStatsService,
    athlete_profile_id: UUID,
    *,
    reference_date_provider=date.today,
) -> AITool:
    """Expose les statistiques calculées par le domaine training."""

    def execute(arguments: BaseModel) -> dict:
        period_arguments = (
            {"days": arguments.nb_days}
            if arguments.nb_days is not None
            else {}
        )
        stats = service.calculate_days(
            athlete_profile_id,
            reference_date_provider(),
            **period_arguments,
            include_reference_day=not arguments.exclude_current_day,
        )
        return stats.history_summary()

    return AITool(
        name="training_history",
        description=(
            "Retourne le bilan réel des entraînements sur la période demandée. "
            "nb_days est facultatif : en son absence, le domaine applique sa fenêtre par défaut. "
            "Par défaut, la date de référence est incluse ; "
            "exclude_current_day=true permet d'analyser uniquement les jours entièrement écoulés. "
            "Les métriques précisent leur couverture. "
            "Quand la couverture est partielle, observed_value est le sous-total des seules séances "
            "renseignées : l'annoncer explicitement comme partiel, jamais comme total de période."
        ),
        arguments_model=TrainingHistoryArguments,
        handler=execute,
    )
