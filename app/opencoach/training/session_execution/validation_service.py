"""Validation explicite d'une séance réalisée."""

from __future__ import annotations

from dataclasses import dataclass, replace
from uuid import UUID

from opencoach.database.repositories.activity import (
    ActivityRepository,
)
from opencoach.database.repositories.activity_detail import (
    ActivityDetailRepository,
)
from opencoach.database.repositories.training_session import (
    TrainingSessionRepository,
)
from opencoach.planning.sessions.prescription.integrity import (
    TrainingSessionPrescriptionIntegrityError,
    validate_training_session_prescription,
)
from opencoach.training.session_execution.analyzer import (
    analyze_session_execution,
)
from opencoach.training.session_execution.persisted_analysis import (
    PersistedSessionExecutionAnalysis,
)
from opencoach.training.session_execution.validation_writer import (
    TrainingSessionValidationWriter,
)


class TrainingSessionValidationError(RuntimeError):
    """Erreur métier lors de la validation d'une séance."""


class TrainingSessionNotFoundError(
    TrainingSessionValidationError
):
    pass


class TrainingSessionActivityNotFoundError(
    TrainingSessionValidationError
):
    pass


class TrainingSessionAlreadyValidatedError(
    TrainingSessionValidationError
):
    pass


class TrainingSessionMissingActivityDetailError(
    TrainingSessionValidationError
):
    pass


class TrainingSessionInvalidPrescriptionError(
    TrainingSessionValidationError
):
    pass


@dataclass(frozen=True, slots=True)
class TrainingSessionValidationResult:
    session: object
    analysis: PersistedSessionExecutionAnalysis



@dataclass(slots=True)
class ValidateTrainingSessionService:
    """Valide l'association choisie explicitement par l'athlète."""

    training_session_repository: TrainingSessionRepository
    activity_repository: ActivityRepository
    activity_detail_repository: ActivityDetailRepository
    validation_writer: TrainingSessionValidationWriter

    def execute(
        self,
        *,
        athlete_profile_id: UUID,
        training_session_id: UUID,
        activity_id: UUID,
    ) -> TrainingSessionValidationResult:
        """Associe, analyse et valide une séance choisie par l'athlète."""

        session = (
            self.training_session_repository
            .get_session(
                athlete_profile_id,
                training_session_id,
            )
        )

        if session is None:
            raise TrainingSessionNotFoundError(
                "Séance introuvable."
            )

        if (
            session.status == "completed"
            or session.activity_id is not None
        ):
            raise TrainingSessionAlreadyValidatedError(
                "Cette séance possède déjà une activité validée."
            )

        activity = (
            self.activity_repository
            .get_activity(
                athlete_profile_id,
                activity_id,
            )
        )

        if activity is None:
            raise TrainingSessionActivityNotFoundError(
                "Activité introuvable."
            )

        if activity.id is None:
            raise TrainingSessionActivityNotFoundError(
                "L'activité doit être persistée."
            )

        try:
            validate_training_session_prescription(
                session
            )
        except TrainingSessionPrescriptionIntegrityError as exc:
            raise TrainingSessionInvalidPrescriptionError(
                "La séance ne possède pas une "
                "prescription exploitable."
            ) from exc

        detail = (
            self.activity_detail_repository
            .get_activity_detail(
                athlete_profile_id,
                activity.id,
            )
        )

        if detail is None:
            raise TrainingSessionMissingActivityDetailError(
                "Les données détaillées de cette activité "
                "ne sont pas encore disponibles."
            )

        # Important :
        # l'analyse est réalisée AVANT toute modification de la séance.
        assessment = analyze_session_execution(
            session,
            activity,
            detail,
        )

        validated_session = replace(
            session,
            activity_id=activity.id,
            status="completed",
        )

        (
            persisted_session,
            persisted_analysis,
        ) = self.validation_writer.persist(
            athlete_profile_id=(
                athlete_profile_id
            ),
            session=validated_session,
            assessment=assessment,
        )

        return TrainingSessionValidationResult(
            session=persisted_session,
            analysis=persisted_analysis,
        )
