"""Port transactionnel de validation d'une séance."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from opencoach.models import TrainingSession
from opencoach.training.session_execution.models import (
    SessionExecutionAssessment,
)
from opencoach.training.session_execution.persisted_analysis import (
    PersistedSessionExecutionAnalysis,
)


class TrainingSessionValidationWriter(ABC):
    """Persiste atomiquement séance validée et débriefing."""

    @abstractmethod
    def persist(
        self,
        *,
        athlete_profile_id: UUID,
        session: TrainingSession,
        assessment: SessionExecutionAssessment,
    ) -> tuple[
        TrainingSession,
        PersistedSessionExecutionAnalysis,
    ]:
        """Sauvegarde tout ou rien."""
        raise NotImplementedError
