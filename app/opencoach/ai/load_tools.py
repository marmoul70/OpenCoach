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
        estimated_load_data_count = getattr(
            stats, "estimated_load_data_count", 0
        )
        available_load_sessions = (
            stats.measured_load_data_count + estimated_load_data_count
        )
        planned_sessions = load.planned_sessions_count

        # La couverture est calculée par le modèle métier TrainingStats,
        # puis seulement présentée ici dans le contrat conversationnel.
        duration_data_count = stats.duration_data_count
        distance_data_count = stats.distance_data_count
        elevation_data_count = stats.elevation_data_count
        load_coverage = stats.coverage(available_load_sessions)
        duration_coverage = stats.coverage(duration_data_count)
        distance_coverage = stats.coverage(distance_data_count)
        elevation_coverage = stats.coverage(elevation_data_count)
        volume = {
            "duration_minutes": (
                getattr(stats, "total_duration_minutes", None)
                if actual_sessions > 0 and duration_data_count == actual_sessions
                else None
            ),
            "partial_duration_minutes": (
                getattr(stats, "total_duration_minutes", None)
                if duration_data_count > 0 and duration_data_count < actual_sessions
                else None
            ),
            "duration_coverage": duration_coverage,
            "distance_km": (
                getattr(stats, "total_distance_km", None)
                if actual_sessions > 0 and distance_data_count == actual_sessions
                else None
            ),
            "partial_distance_km": (
                getattr(stats, "total_distance_km", None)
                if distance_data_count > 0 and distance_data_count < actual_sessions
                else None
            ),
            "distance_coverage": distance_coverage,
            "elevation_gain_m": (
                getattr(stats, "total_elevation_gain_m", None)
                if actual_sessions > 0 and elevation_data_count == actual_sessions
                else None
            ),
            "partial_elevation_gain_m": (
                getattr(stats, "total_elevation_gain_m", None)
                if elevation_data_count > 0 and elevation_data_count < actual_sessions
                else None
            ),
            "elevation_coverage": elevation_coverage,
            "activity_count": getattr(stats, "activities_count", actual_sessions - stats.manual_sessions_count),
            "manual_session_count": stats.manual_sessions_count,
        }

        coverage_status = load_coverage["status"]
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
            "volume": volume,
            "sessions": {
                "planned": planned_sessions,
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
                "planned_total": load.planned_load_total,
                "actual_total": stats.total_load if has_complete_load else None,
                "partial_observed_total": (
                    stats.total_load if coverage_status == "partial" else None
                ),
                "measured_total": stats.measured_load if has_complete_load else None,
                "estimated_total": stats.estimated_load if has_complete_load else None,
                "delta_total": load.load_delta_total if has_complete_load else None,
                "ratio": load.load_ratio if has_complete_load else None,
                "coverage": {
                    **load_coverage,
                    "measured_sessions": stats.measured_load_data_count,
                    "estimated_manual_sessions": estimated_load_data_count,
                },
                "unit": "load_points",
            },
            "planning_coverage": {
                "covered_days": load.planning_covered_days,
                "unplanned_days": load.unplanned_days,
                "ratio": load.planning_coverage_ratio,
                "meaning": (
                    "Jours sans couverture de planning OpenCoach. Cela ne signifie "
                    "ni absence d'entraînement, ni absence d'activité importée."
                ),
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
            "Une charge réelle sans couverture complète n'est jamais présentée comme un total fiable. "
            "Les résultats proviennent exclusivement des services métier et des données centralisées dans OpenCoach."
        ),
        arguments_model=TrainingLoadArguments,
        handler=execute,
    )
