"""Outil de synthèse de charge récente, basé sur les services métier existants."""
from __future__ import annotations

from datetime import date, timedelta
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from opencoach.ai.tool_engine import AITool
from opencoach.training import RecentTrainingLoadService, TrainingStatsService


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
    training_stats_service: TrainingStatsService,
    athlete_profile_id: UUID,
    *,
    reference_date_provider=date.today,
    wellness_repository=None,
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
        stats = training_stats_service.calculate(
            athlete_profile_id,
            start_date,
            end_date,
        )

        actual_sessions = stats.sessions_count
        available_load_sessions = (
            stats.measured_load_data_count + stats.manual_sessions_count
        )
        planned_sessions = sum(day.planned_sessions_count for day in load.days)

        coros_load_days = []
        if wellness_repository is not None:
            for wellness_day in wellness_repository.list_range(
                athlete_profile_id,
                start_date,
                end_date,
                provider="coros",
            ):
                atl = wellness_day.fatigue_atl
                ctl = wellness_day.fitness_ctl
                if atl is None and ctl is None:
                    continue
                coros_load_days.append({
                    "date": wellness_day.date.isoformat(),
                    "atl_short_term_load": atl,
                    "ctl_long_term_load": ctl,
                    "load_ratio": (
                        round(atl / ctl, 2)
                        if atl is not None and ctl is not None and ctl > 0
                        else None
                    ),
                })
        coros_load_days.sort(key=lambda item: item["date"])

        if actual_sessions == 0:
            coverage_status = "no_sessions"
        elif available_load_sessions == 0:
            coverage_status = "unavailable"
        elif available_load_sessions < actual_sessions:
            coverage_status = "partial"
        else:
            coverage_status = "complete"

        has_complete_load = coverage_status == "complete"

        daily = [
            {
                "date": day.date.isoformat(),
                "status": (
                    day.status
                    if has_complete_load or day.actual_sessions_count == 0
                    else "load_data_incomplete"
                ),
                "planned_load": day.planned_load,
                "actual_load": (
                    day.actual_load
                    if has_complete_load and day.actual_sessions_count
                    else None
                ),
                "load_delta": (
                    day.load_delta
                    if has_complete_load and day.actual_sessions_count
                    else None
                ),
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
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "nb_days": nb_days,
                "inclusive": True,
            },
            "sessions": {
                "planned": planned_sessions,
                "actual": actual_sessions,
            },
            "coros_training_load": {
                "source": "COROS Training Load Assessment",
                "semantics": (
                    "Charge court terme ATL et charge long terme CTL fournies par COROS. "
                    "Ces indicateurs de forme ne sont pas des charges par séance et ne "
                    "sont jamais additionnés au total de charge des activités."
                ),
                "coverage": {
                    "available_days": len(coros_load_days),
                    "expected_days": nb_days,
                    "status": (
                        "complete" if len(coros_load_days) == nb_days
                        else "partial" if coros_load_days
                        else "unavailable"
                    ),
                },
                "daily": coros_load_days,
                "latest": coros_load_days[-1] if coros_load_days else None,
            },
            "load": {
                "planned_total": load.planned_load_total,
                "actual_total": load.actual_load_total if has_complete_load else None,
                "partial_observed_total": (
                    load.actual_load_total if coverage_status == "partial" else None
                ),
                "measured_total": (
                    round(sum(day.measured_load for day in load.days), 2)
                    if has_complete_load else None
                ),
                "estimated_total": (
                    round(sum(day.estimated_load for day in load.days), 2)
                    if has_complete_load else None
                ),
                "delta_total": load.load_delta_total if has_complete_load else None,
                "ratio": load.load_ratio if has_complete_load else None,
                "coverage": {
                    "available_sessions": available_load_sessions,
                    "total_sessions": actual_sessions,
                    "status": coverage_status,
                },
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
            "Une charge réelle sans couverture complète n'est jamais présentée comme un total fiable."
        ),
        arguments_model=TrainingLoadArguments,
        handler=execute,
    )
