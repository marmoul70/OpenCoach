from abc import ABC, abstractmethod
from datetime import date
from uuid import UUID

from opencoach.models import Activity, TrainingSession


class TrainingSessionRepository(ABC):
    """Abstraction de persistance des séances planifiées."""

    @abstractmethod
    def save_session(
        self,
        athlete_profile_id: UUID,
        session: TrainingSession,
    ) -> TrainingSession:
        """Crée ou met à jour une séance."""
        raise NotImplementedError

    @abstractmethod
    def delete_session(
        self,
        athlete_profile_id: UUID,
        session_id: UUID,
    ) -> None:
        """Supprime une séance planifiée."""
        raise NotImplementedError

    @abstractmethod
    def get_session(
        self,
        athlete_profile_id: UUID,
        session_id: UUID,
    ) -> TrainingSession | None:
        """Retourne une séance par identifiant."""
        raise NotImplementedError

    @abstractmethod
    def list_sessions_between(
        self,
        athlete_profile_id: UUID,
        start_date: date,
        end_date: date,
    ) -> list[TrainingSession]:
        """Retourne les séances comprises dans une période."""
        raise NotImplementedError

    @abstractmethod
    def update_status(
        self,
        athlete_profile_id: UUID,
        session_id: UUID,
        status: str,
    ) -> TrainingSession:
        """Met à jour le statut d'une séance."""
        raise NotImplementedError

    @abstractmethod
    def link_activity(
        self,
        athlete_profile_id: UUID,
        session_id: UUID,
        activity_id: UUID | None,
    ) -> TrainingSession:
        """Associe ou désassocie une activité à une séance."""
        raise NotImplementedError

    @abstractmethod
    def list_candidate_activities_for_date(
        self,
        athlete_profile_id: UUID,
        session_date: date,
    ) -> list[Activity]:
        """Retourne les activités détectées le même jour."""
        raise NotImplementedError

    @abstractmethod
    def list_unlinked_activities_for_date(
        self,
        athlete_profile_id: UUID,
        session_date: date,
    ) -> list[Activity]:
        """Retourne les activités du jour non liées à une séance."""
