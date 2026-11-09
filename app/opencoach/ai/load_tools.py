"""Outil de synthèse de charge récente, basé sur les services métier existants."""
from __future__ import annotations

from datetime import date, timedelta
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from opencoach.ai.tool_engine import AITool
from opencoach.training import RecentTrainingLoadService


class TrainingLoadArguments(BaseModel):
    """Période bornée pour l'analyse de charge."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    nb_days: int = Field(
        ge=1,
        le=90,
        description="Nombre de jours calendaires précédant la date de référence.",
    )


def build_training_load_tool(
    service: RecentTrainingLoadService,
    athlete_profile_id: UUID,
    *,
    reference_date_provider=date.today,
) -> AITool:
    """Construit l'outil de charge pour l'athlète authentifié."""

    def execute(arguments: BaseModel) -> dict:
        nb_days = arguments.nb_days
        target_date = reference_date_provider()
        start_date = target_date - timedelta(days=nb_days)
        end_date = target_date - timedelta(days=1)
        load = service.calculate(
            athlete_profile_id,
            target_date,
            days=nb_days,
        )

        actual_sessions = sum(day.actual_sessions_count for day in load.days)
        planned_sessions = sum(day.planned_sessions_count for day in load.days)
        has_actual_data = actual_sessions > 0

        daily = [
            {
                "date": day.date.isoformat(),
                "status": day.status,
                "planned_load": day.planned_load,
                "actual_load": day.actual_load if day.actual_sessions_count else None,
                "load_delta": day.load_delta if day.actual_sessions_count else None,
                "planned_sessions": day.planned_sessions_count,
                "actual_sessions": day.actual_sessions_count,
            }
            for day in sorted(load.days, key=lambda item: item.date)
        ]

        warnings = []
        if load.unplanned_days:
            warnings.append(
                f"Le planning OpenCoach ne couvre pas {load.unplanned_days} jour(s) de la période."
            )
        if not has_actual_data:
            warnings.append(
                "Aucune séance réalisée enregistrée : la charge réelle est indisponible, pas égale à zéro."
            )

        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "nb_days": nb_days,
                "inclusive": True,
            },
            "sessions": {
                "planned": planned_sessions,
                "actual": actual_sessions,
            },
            "load": {
                "planned_total": load.planned_load_total,
                "actual_total": load.actual_load_total if has_actual_data else None,
                "measured_total": (
                    round(sum(day.measured_load for day in load.days), 2)
                    if has_actual_data else None
                ),
                "estimated_total": (
                    round(sum(day.estimated_load for day in load.days), 2)
                    if has_actual_data else None
                ),
                "delta_total": load.load_delta_total if has_actual_data else None,
                "ratio": load.load_ratio if has_actual_data else None,
                "unit": "load_points",
            },
            "planning_coverage": {
                "covered_days": load.planning_covered_days,
                "unplanned_days": load.unplanned_days,
                "ratio": load.planning_coverage_ratio,
            },
            "distribution": {
                "above_plan_days": load.above_plan_days,
                "on_plan_days": load.on_plan_days,
                "below_plan_days": load.below_plan_days,
                "broken_rest_days": load.broken_rest_days,
                "respected_rest_days": load.respected_rest_days,
            },
            "daily": daily,
            "warnings": warnings,
        }

    return AITool(
        name="training_load",
        description=(
            "Retourne la charge d'entraînement réelle et prévue sur les nb_days derniers "
            "jours calendaires inclusifs, avec écarts quotidiens et couverture du planning. "
            "nb_days est obligatoire : demande la période si elle manque et attends la réponse. "
            "Une charge réelle sans séance enregistrée est indisponible, pas égale à zéro."
        ),
        arguments_model=TrainingLoadArguments,
        handler=execute,
    )
