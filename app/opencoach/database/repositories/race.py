from abc import ABC, abstractmethod
from datetime import date
from uuid import UUID

from opencoach.models import Race
from opencoach.models import Activity, Race

class RaceRepository(ABC):
    """Abstraction de persistance des courses."""

    @abstractmethod
    def save_race(
        self,
        athlete_profile_id: UUID,
        race: Race,
    ) -> Race:
        """Crée ou met à jour une course."""
        raise NotImplementedError

    @abstractmethod
    def get_race(
        self,
        athlete_profile_id: UUID,
        race_id: UUID,
    ) -> Race | None:
        """Retourne une course par identifiant."""
        raise NotImplementedError

    @abstractmethod
    def delete_race(
        self,
        athlete_profile_id: UUID,
        race_id: UUID,
    ) -> None:
        """Supprime une course."""
        raise NotImplementedError

    @abstractmethod
    def list_races_between(
        self,
        athlete_profile_id: UUID,
        start_date: date,
        end_date: date,
    ) -> list[Race]:
        """Retourne les courses comprises dans une période."""
        raise NotImplementedError

    @abstractmethod
    def list_upcoming_races(
        self,
        athlete_profile_id: UUID,
        from_date: date,
    ) -> list[Race]:
        """Retourne les prochaines courses planifiées."""
        raise NotImplementedError

    @abstractmethod
    def get_next_primary_race(
        self,
        athlete_profile_id: UUID,
        from_date: date,
    ) -> Race | None:
        """Retourne le prochain objectif prioritaire."""
        raise NotImplementedError

    @abstractmethod
    def list_training_races_between(
        self,
        athlete_profile_id: UUID,
        start_date: date,
        end_date: date,
    ) -> list[Race]:
        """Retourne les courses d'entraînement dans une période."""
        raise NotImplementedError

    @abstractmethod
    def list_training_races_before(
        self,
        athlete_profile_id: UUID,
        from_date: date,
        primary_date: date,
    ) -> list[Race]:
        """Retourne les courses d'entraînement avant un objectif."""
        raise NotImplementedError

    @abstractmethod
    def link_activity(
        self,
        athlete_profile_id: UUID,
        race_id: UUID,
        activity_id: UUID | None,
    ) -> Race:
        """Associe ou désassocie une activité à une course."""
        raise NotImplementedError

    @abstractmethod
    def list_candidate_activities_for_date(
        self,
        athlete_profile_id: UUID,
        race_date: date,
    ) -> list[Activity]:
        """Retourne les activités réalisées le jour de la course."""
        raise NotImplementedError
