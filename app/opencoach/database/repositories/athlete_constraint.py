from abc import ABC, abstractmethod
from datetime import date
from uuid import UUID

from opencoach.models import AthleteConstraint


class AthleteConstraintRepository(ABC):
    """Abstraction de persistance des contraintes temporaires."""

    @abstractmethod
    def save_constraint(
        self,
        athlete_profile_id: UUID,
        constraint: AthleteConstraint,
    ) -> AthleteConstraint:
        """Crée ou met à jour une contrainte."""
        raise NotImplementedError

    @abstractmethod
    def get_constraint(
        self,
        athlete_profile_id: UUID,
        constraint_id: UUID,
    ) -> AthleteConstraint | None:
        """Retourne une contrainte par identifiant."""
        raise NotImplementedError

    @abstractmethod
    def delete_constraint(
        self,
        athlete_profile_id: UUID,
        constraint_id: UUID,
    ) -> None:
        """Supprime une contrainte."""
        raise NotImplementedError

    @abstractmethod
    def list_overlapping(
        self,
        athlete_profile_id: UUID,
        start_date: date,
        end_date: date,
    ) -> list[AthleteConstraint]:
        """Retourne les contraintes chevauchant une période."""
        raise NotImplementedError
