"""Analyse métier de préparation d'une course future.

Ce service appartient au Coach et reste utilisable sans le moteur conversationnel.
"""
from __future__ import annotations

from datetime import date, timedelta
from uuid import UUID

from opencoach.database.repositories import RaceRepository
from opencoach.services.profile import ProfileService
from opencoach.training import TrainingStatsService


class RacePreparationService:
    DEFAULT_CALENDAR_HORIZON_DAYS = 180

    """Confronte les exigences d'une course à l'entraînement réellement observé."""

    def __init__(
        self,
        race_repository: RaceRepository,
        profile_service: ProfileService,
        training_stats_service: TrainingStatsService,
        athlete_profile_id: UUID,
        *,
        reference_date_provider=date.today,
    ) -> None:
        self.race_repository = race_repository
        self.profile_service = profile_service
        self.training_stats_service = training_stats_service
        self.athlete_profile_id = athlete_profile_id
        self.reference_date_provider = reference_date_provider

    def list_calendar(
        self,
        *,
        start_date: date | None = None,
        horizon_days: int | None = None,
    ) -> dict:
        """Retourne le calendrier de courses de l'athlète sur une fenêtre inclusive."""
        effective_horizon = self.DEFAULT_CALENDAR_HORIZON_DAYS if horizon_days is None else horizon_days
        if not 1 <= effective_horizon <= 365:
            raise ValueError("L'horizon du calendrier doit être compris entre 1 et 365 jours.")

        period_start = start_date or self.reference_date_provider()
        period_end = period_start + timedelta(days=effective_horizon - 1)
        races = self.race_repository.list_races_between(
            self.athlete_profile_id,
            period_start,
            period_end,
        )
        return {
            "status": "ok" if races else "empty",
            "period": {
                "start_date": period_start.isoformat(),
                "end_date": period_end.isoformat(),
                "horizon_days": effective_horizon,
                "inclusive": True,
            },
            "race_count": len(races),
            "races": [
                {
                    "race_id": str(race.id),
                    "date": race.date.isoformat(),
                    "days_from_period_start": (race.date - period_start).days,
                    "name": race.name[:160] if race.name is not None else None,
                    "location": race.location[:120] if race.location is not None else None,
                    "race_type": race.race_type[:50] if race.race_type is not None else None,
                    "priority": race.priority,
                    "status": race.status,
                    "distance_km": race.distance_km,
                    "elevation_gain_m": race.elevation_gain_m,
                    "target_time_minutes": race.target_time_minutes,
                    "actual_distance_km": race.actual_distance_km,
                    "actual_elevation_gain_m": race.actual_elevation_gain_m,
                    "actual_time_minutes": race.actual_time_minutes,
                    "has_linked_activity": race.activity_id is not None,
                }
                for race in races
            ],
        }

    def analyze(self, race_id: UUID, history_days: int) -> dict:
        if not 7 <= history_days <= 180:
            raise ValueError("La période d'historique doit être comprise entre 7 et 180 jours.")
        race_repository = self.race_repository
        profile_service = self.profile_service
        training_stats_service = self.training_stats_service
        athlete_profile_id = self.athlete_profile_id
        reference_date_provider = self.reference_date_provider
        reference_date = reference_date_provider()
        race = race_repository.get_race(
            athlete_profile_id,
            race_id,
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
        
        start_date = reference_date - timedelta(days=history_days - 1)
        end_date = reference_date
        stats = training_stats_service.calculate(
            athlete_profile_id,
            start_date,
            end_date,
        )
        
        # TrainingStatsService est la source canonique des totaux et de leur
        # couverture. Ne pas relire les repositories ni reconstruire ces
        # comptages ici : cela risquerait de diverger de ses règles métier.
        included_sessions = stats.sessions_count
        duration_coverage = stats.duration_data_count
        distance_coverage = stats.distance_data_count
        elevation_coverage = stats.elevation_data_count
        available_load_sessions = (
            stats.measured_load_data_count + stats.estimated_load_data_count
        )
        load_coverage = stats.coverage(available_load_sessions)

        def metric(value: float | int, available: int, unit: str) -> dict:
            coverage = stats.coverage(available)
            reliable_value = value if coverage["status"] == "complete" else None
            return {
                "total": reliable_value,
                "weekly_equivalent": (
                    round(reliable_value * 7 / history_days, 2)
                    if reliable_value is not None else None
                ),
                "unit": unit,
                "coverage": coverage,
            }
        
        profile = profile_service.get_profile()
        days_to_race = (race.date - reference_date).days
        distance = race.distance_km
        elevation = race.elevation_gain_m
        
        missing_race_data = []
        if distance is None or distance <= 0:
            missing_race_data.append("distance_km")
        if elevation is None:
            missing_race_data.append("elevation_gain_m")
        
        missing_optional_race_data = (
            ["target_time_minutes"] if race.target_time_minutes is None else []
        )
        
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
        
        recent_training = {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": history_days,
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
                    if load_coverage["status"] == "complete"
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
                    if load_coverage["status"] == "partial"
                    else None
                ),
                "unit": "load_points",
                "coverage": (
                    "partial_or_unavailable"
                    if load_coverage["status"] in {"partial", "unavailable"}
                    else load_coverage["status"]
                ),
            },
        }
        
        missing_profile_data = []
        if profile is None:
            missing_profile_data.append("athlete_profile")
            capacity = None
        else:
            capacity = {
                "weekly_sessions_target": profile.training.weekly_sessions,
                "weekly_duration_target_minutes": profile.training.weekly_duration_minutes,
                "weekly_distance_target_km": profile.training.weekly_distance_km,
                "experience": profile.training.experience,
                "sport_disciplines": list(profile.training.sport_disciplines or []),
            }
            for key, value in (
                ("weekly_sessions", profile.training.weekly_sessions),
                ("weekly_duration_minutes", profile.training.weekly_duration_minutes),
                ("weekly_distance_km", profile.training.weekly_distance_km),
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
                "missing_optional_race_fields": missing_optional_race_data,
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
