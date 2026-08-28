"""Repository des propositions de tests physiologiques."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from uuid import UUID

from opencoach.physiology.testing.proposal import (
    PhysiologicalTestProposal,
)


class PhysiologicalTestProposalRepositoryError(
    RuntimeError
):
    """Erreur de persistance d'une proposition de test."""


class PhysiologicalTestProposalRepository(ABC):
    """Interface de persistance des propositions de tests."""

    @abstractmethod
    def save(
        self,
        proposal: PhysiologicalTestProposal,
    ) -> PhysiologicalTestProposal:
        """Crée ou met à jour une proposition."""

        raise NotImplementedError

    @abstractmethod
    def get(
        self,
        athlete_profile_id: UUID,
        proposal_id: UUID,
    ) -> PhysiologicalTestProposal | None:
        """Charge une proposition par identifiant."""

        raise NotImplementedError

    @abstractmethod
    def get_pending(
        self,
        athlete_profile_id: UUID,
    ) -> tuple[
        PhysiologicalTestProposal,
        ...,
    ]:
        """Retourne les propositions attendant une décision."""

        raise NotImplementedError

    @abstractmethod
    def list_since(
        self,
        athlete_profile_id: UUID,
        since: date,
    ) -> tuple[
        PhysiologicalTestProposal,
        ...,
    ]:
        """Retourne l'historique récent des propositions."""

        raise NotImplementedError
