"""Analyse déterministe d'un objectif de course et de la progression récente."""

from __future__ import annotations

from datetime import date, timedelta
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from opencoach.ai.tool_engine import AITool
from opencoach.database.models import AthleteProfile, Race
from opencoach.training import TrainingStatsService


class RacePreparationArguments(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    race_id: UUID = Field(description="Identifiant de la course obtenu via race_calendar.")
    history_days: int = Field(
        ge=7,
        le=180,
        description="Nombre de jours calendaires d'historique récent à analyser. Obligatoire.",
    )


def build_race_preparation_tool(
    session: Session,
    training_stats_service: TrainingStatsService,
    athlete_profile_id: UUID,
    *,
    reference_date_provider=date.today,
) -> AITool:
    """Compare les exigences d'une course à la progression récente documentée."""

    def execute(arguments: BaseModel) -> dict:
        reference_date = reference_date_provider()
        race = session.scalar(
            select(Race).where(
                Race.id == arguments.race_id,
                Race.athlete_profile_id == athlete_profile_id,
            )
        )
        if race is None:
            return {
                "status": "not_found",
                "message": "Cette course n'existe pas dans le calendrier de l'athlète authentifié.",
            }

        if race.date < reference_date:
            return {
                "status": "past_event",
                "reference_date": reference_date.isoformat(),
                "race": {
                    "race_id": str(race.id),
                    "date": race.date.isoformat(),
                    "name": race.name[:160],
                    "status": race.status,
                },
                "message": (
                    "La date de cette course est passée. Utilise son bilan de résultat "
                    "ou son activité liée plutôt qu'une analyse de préparation future."
                ),
            }

        start_date = reference_date - timedelta(days=arguments.history_days - 1)
        end_date = reference_date
        stats = training_stats_service.calculate(
            athlete_profile_id,
            start_date,
            end_date,
        )

        activities = training_stats_service.activity_repository.list_activities_between(
            athlete_profile_id,
            start_date,
            end_date,
        )
        sessions = training_stats_service.training_session_repository.list_sessions_between(
            athlete_profile_id,
            start_date,
            end_date,
        )
        manual_sessions = [
            item for item in sessions
            if item.status == "completed"
            and item.activity_id is None
            and item.type != "rest"
        ]
        included_sessions = len(activities) + len(manual_sessions)

        duration_coverage = sum(
            1 for item in activities
            if item.moving_time_seconds is not None
            or item.elapsed_time_seconds is not None
        ) + len(manual_sessions)
        distance_coverage = sum(
            1 for item in activities if item.distance_m is not None
        ) + sum(
            1 for item in manual_sessions if item.distance_km is not None
        )
        elevation_coverage = sum(
            1 for item in activities if item.elevation_gain_m is not None
        ) + sum(
            1 for item in manual_sessions if item.elevation_gain_m is not None
        )

        def metric(value: float | int, available: int, unit: str) -> dict:
            if included_sessions == 0:
                coverage_status = "no_sessions"
            elif available == 0:
                coverage_status = "unavailable"
            elif available < included_sessions:
                coverage_status = "partial"
            else:
                coverage_status = "complete"

            reliable_value = value if coverage_status == "complete" else None
            return {
                "total": reliable_value,
                "weekly_equivalent": (
                    round(reliable_value * 7 / arguments.history_days, 2)
                    if reliable_value is not None else None
                ),
                "unit": unit,
                "coverage": {
                    "available_sessions": available,
                    "total_sessions": included_sessions,
                    "status": coverage_status,
                },
            }

        profile = session.scalar(
            select(AthleteProfile).where(AthleteProfile.id == athlete_profile_id)
        )
        days_to_race = (race.date - reference_date).days
        distance = race.distance_km
        elevation = race.elevation_gain_m

        missing_race_data = []
        if distance is None or distance <= 0:
            missing_race_data.append("distance_km")
        if elevation is None:
            missing_race_data.append("elevation_gain_m")

        course_profile = {
            "distance_km": distance,
            "elevation_gain_m": elevation,
            "elevation_density_m_per_km": (
                round(elevation / distance, 1)
                if elevation is not None and distance is not None and distance > 0
                else None
            ),
            "target_time_minutes": race.target_time_minutes,
        }

        available_load_sessions = sum(
            1 for item in activities if item.training_load is not None
        ) + len(manual_sessions)

        recent_training = {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": arguments.history_days,
                "inclusive": True,
            },
            "sessions_count": included_sessions,
            "duration": metric(
                stats.total_duration_minutes,
                duration_coverage,
                "minutes",
            ),
            "distance": metric(
                stats.total_distance_km,
                distance_coverage,
                "km",
            ),
            "elevation_gain": metric(
                stats.total_elevation_gain_m,
                elevation_coverage,
                "m",
            ),
            "load": {
                "measured": (
                    stats.measured_load
                    if included_sessions > 0 and available_load_sessions == included_sessions
                    else None
                ),
                "estimated": (
                    stats.estimated_load
                    if included_sessions > 0 and available_load_sessions == included_sessions
                    else None
                ),
                "total": (
                    stats.total_load
                    if included_sessions > 0 and available_load_sessions == included_sessions
                    else None
                ),
                "partial_observed_total": (
                    stats.total_load
                    if 0 < available_load_sessions < included_sessions
                    else None
                ),
                "unit": "load_points",
                "coverage": (
                    "no_sessions"
                    if included_sessions == 0
                    else "complete"
                    if available_load_sessions == included_sessions
                    else "partial_or_unavailable"
                ),
            },
        }

        missing_profile_data = []
        if profile is None:
            missing_profile_data.append("athlete_profile")
            capacity = None
        else:
            capacity = {
                "weekly_sessions_target": profile.weekly_sessions,
                "weekly_duration_target_minutes": profile.weekly_duration_minutes,
                "weekly_distance_target_km": profile.weekly_distance_km,
                "experience": profile.experience,
                "sport_disciplines": list(profile.sport_disciplines or []),
            }
            for key, value in (
                ("weekly_sessions", profile.weekly_sessions),
                ("weekly_duration_minutes", profile.weekly_duration_minutes),
                ("weekly_distance_km", profile.weekly_distance_km),
            ):
                if value is None:
                    missing_profile_data.append(key)

        metric_coverage = [
            recent_training["duration"]["coverage"]["status"],
            recent_training["distance"]["coverage"]["status"],
            recent_training["elevation_gain"]["coverage"]["status"],
            recent_training["load"]["coverage"],
        ]
        complete_analysis = (
            not missing_race_data
            and not missing_profile_data
            and included_sessions > 0
            and all(item == "complete" for item in metric_coverage)
        )

        return {
            "status": "ok" if complete_analysis else "partial",
            "reference_date": reference_date.isoformat(),
            "days_to_race": days_to_race,
            "race": {
                "race_id": str(race.id),
                "date": race.date.isoformat(),
                "name": race.name[:160],
                "race_type": race.race_type,
                "priority": race.priority,
                "status": race.status,
                "course_profile": course_profile,
            },
            "athlete_capacity": capacity,
            "recent_training": recent_training,
            "data_quality": {
                "missing_race_fields": missing_race_data,
                "missing_profile_fields": missing_profile_data,
                "sessions_included": included_sessions,
                "metric_coverage": {
                    "duration": metric_coverage[0],
                    "distance": metric_coverage[1],
                    "elevation_gain": metric_coverage[2],
                    "load": metric_coverage[3],
                },
                "interpretation": (
                    "Les totaux et moyennes hebdomadaires ne sont exposés que si "
                    "toutes les séances incluses disposent de la métrique. Une "
                    "couverture partielle n'est jamais extrapolée."
                ),
            },
            "coaching_rules": [
                "Ne pas produire de score de préparation ou de probabilité de réussite.",
                "Distinguer les objectifs hebdomadaires du profil des volumes réellement observés.",
                "Ne pas assimiler les moyennes récentes à une recommandation de charge future.",
                "Ne pas conclure à une aptitude médicale.",
                "Si les données de course, de profil ou d'entraînement sont incomplètes, les demander ou annoncer explicitement la limite.",
            ],
        }

    return AITool(
        name="race_preparation_analysis",
        description=(
            "Analyse une course future du calendrier de l'athlète authentifié en "
            "croisant ses caractéristiques (distance, D+, date, objectif) avec le "
            "profil d'entraînement et l'historique réellement observé. race_id doit "
            "être obtenu via race_calendar. history_days est obligatoire (7 à 180) : "
            "si la période n'est pas précisée, demande à l'utilisateur combien de "
            "jours analyser. Les totaux et moyennes sont masqués si la couverture "
            "des métriques est incomplète. Aucun score de préparation n'est inventé."
        ),
        arguments_model=RacePreparationArguments,
        handler=execute,
    )
