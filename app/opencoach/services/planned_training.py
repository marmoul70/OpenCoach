"""Services de consultation du planning d'entraînement."""

from __future__ import annotations

from datetime import date, timedelta
from uuid import UUID

from opencoach.database.repositories import TrainingSessionRepository
from opencoach.models import TrainingSession


class PlannedTrainingService:
    """Centralise les lectures et agrégats des séances planifiées."""

    def __init__(
        self,
        repository: TrainingSessionRepository,
        athlete_profile_id: UUID,
        *,
        reference_date_provider=date.today,
    ) -> None:
        self.repository = repository
        self.athlete_profile_id = athlete_profile_id
        self.reference_date_provider = reference_date_provider

    def list_between(
        self,
        start_date: date,
        end_date: date,
    ) -> tuple[list[TrainingSession], dict]:
        if end_date < start_date:
            raise ValueError("La date de fin doit être postérieure ou égale à la date de début.")
        if (end_date - start_date).days > 30:
            raise ValueError("La période ne peut pas dépasser 31 jours calendaires.")

        sessions = self.repository.list_sessions_between(
            self.athlete_profile_id,
            start_date,
            end_date,
        )
        distance_values = [
            item.distance_km for item in sessions if item.distance_km is not None
        ]
        elevation_values = [
            item.elevation_gain_m for item in sessions if item.elevation_gain_m is not None
        ]
        summary = {
            "duration_minutes": sum(item.duration_minutes for item in sessions),
            "distance_km": (
                round(sum(distance_values), 2)
                if sessions and len(distance_values) == len(sessions) else None
            ),
            "distance_coverage": f"{len(distance_values)}/{len(sessions)}",
            "elevation_gain_m": (
                round(sum(elevation_values), 1)
                if sessions and len(elevation_values) == len(sessions) else None
            ),
            "elevation_coverage": f"{len(elevation_values)}/{len(sessions)}",
        }
        return sessions, summary

    def next_planned(self) -> tuple[date, TrainingSession | None]:
        reference_date = self.reference_date_provider()
        candidates = self.repository.list_sessions_between(
            self.athlete_profile_id,
            reference_date,
            reference_date + timedelta(days=365),
        )
        session = next(
            (item for item in candidates if item.status == "planned"),
            None,
        )
        return reference_date, session
