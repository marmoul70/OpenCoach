"""Application d'une adaptation quotidienne acceptée.

Ce service constitue la frontière entre :

- la décision explicite de l'athlète ;
- la politique d'adaptation de séance ;
- la persistance de la séance modifiée.

Une seule séance planifiée doit être identifiable sans ambiguïté.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from uuid import UUID

from opencoach.coaching.daily_adaptation import (
    CoachAdaptationProposal,
)
from opencoach.coaching.daily_checkin import (
    AthleteDailyCheckIn,
)
from opencoach.coaching.daily_session_adaptation import (
    DailySessionAdaptationResult,
    adapt_daily_training_session,
)
from opencoach.database.repositories.training_session import (
    TrainingSessionRepository,
)
from opencoach.models import (
    TrainingSession,
)
from opencoach.planning.physiology.snapshot_service import (
    PhysiologicalCalibrationSnapshotService,
)
from opencoach.planning.sessions.prescription.continuous import (
    build_continuous_session_prescription,
)
from opencoach.planning.sessions.prescription.integrity import (
    TrainingSessionPrescriptionIntegrityError,
    validate_training_session_prescription,
)
from opencoach.planning.stimulus.training import (
    TrainingStimulus,
)
from opencoach.services import (
    ProfileService,
)


class DailyAdaptationApplicationError(
    RuntimeError
):
    """Erreur d'application d'une adaptation quotidienne."""


class DailyAdaptationSessionNotFoundError(
    DailyAdaptationApplicationError
):
    """Aucune séance planifiée ne peut être adaptée."""


class DailyAdaptationSessionAmbiguousError(
    DailyAdaptationApplicationError
):
    """Plusieurs séances sont candidates à l'adaptation."""


@dataclass(slots=True)
class ApplyAcceptedDailyAdaptationService:
    """Applique une proposition explicitement acceptée."""

    training_session_repository: (
        TrainingSessionRepository
    )

    profile_service: ProfileService

    physiology_service: (
        PhysiologicalCalibrationSnapshotService
    )

    def execute(
        self,
        *,
        athlete_profile_id: UUID,
        checkin: AthleteDailyCheckIn,
        proposal: CoachAdaptationProposal,
    ) -> DailySessionAdaptationResult:
        """Adapte l'unique séance planifiée du jour."""

        if checkin.id is None:
            raise DailyAdaptationApplicationError(
                "Le check-in doit être persisté."
            )

        if proposal.checkin_id != checkin.id:
            raise DailyAdaptationApplicationError(
                "La proposition ne correspond pas au check-in."
            )

        if not proposal.adaptation_authorized:
            raise DailyAdaptationApplicationError(
                "L'adaptation n'a pas été acceptée "
                "par l'athlète."
            )

        sessions = (
            self.training_session_repository
            .list_sessions_between(
                athlete_profile_id,
                checkin.date,
                checkin.date,
            )
        )

        candidates = tuple(
            session
            for session in sessions
            if (
                session.status == "planned"
                and session.activity_id is None
            )
        )

        if not candidates:
            raise DailyAdaptationSessionNotFoundError(
                "Aucune séance planifiée aujourd'hui "
                "ne peut être adaptée."
            )

        if len(candidates) > 1:
            raise DailyAdaptationSessionAmbiguousError(
                "Plusieurs séances sont planifiées aujourd'hui. "
                "L'athlète doit choisir la séance à adapter."
            )

        original = candidates[0]

        result = adapt_daily_training_session(
            session=original,
            checkin=checkin,
            proposal=proposal,
        )

        if not result.changed:
            return result

        adapted = result.adapted

        if adapted.status != "skipped":
            adapted = (
                self._rebuild_prescription(
                    athlete_profile_id=(
                        athlete_profile_id
                    ),
                    original=result.original,
                    adapted=adapted,
                )
            )

        try:
            validate_training_session_prescription(
                adapted
            )

        except TrainingSessionPrescriptionIntegrityError as exc:
            raise DailyAdaptationApplicationError(
                "L'adaptation produirait une séance "
                "dont la prescription n'est plus "
                "cohérente avec l'objectif."
            ) from exc

        persisted = (
            self.training_session_repository
            .save_session(
                athlete_profile_id,
                adapted,
            )
        )

        return DailySessionAdaptationResult(
            original=result.original,
            adapted=persisted,
            changed=True,
            reasons=result.reasons,
        )


    def _rebuild_prescription(
        self,
        *,
        athlete_profile_id: UUID,
        original: TrainingSession,
        adapted: TrainingSession,
    ) -> TrainingSession:
        """Reconstruit le contrat structuré après adaptation."""

        # ------------------------------------------------------
        # Changement réel de stimulus
        # ------------------------------------------------------

        if adapted.type != original.type:
            try:
                stimulus = TrainingStimulus(
                    adapted.type
                )
            except ValueError as exc:
                raise DailyAdaptationApplicationError(
                    "Le nouveau stimulus de la séance "
                    "n'est pas reconnu par OpenCoach."
                ) from exc

            if stimulus not in {
                TrainingStimulus.RECOVERY,
                TrainingStimulus.AEROBIC_EASY,
                TrainingStimulus.AEROBIC_ENDURANCE,
                TrainingStimulus.LONG_ENDURANCE,
            }:
                raise DailyAdaptationApplicationError(
                    "L'adaptation demande une "
                    "reconstruction de prescription "
                    "non supportée pour ce stimulus."
                )

            athlete = (
                self.profile_service.get_profile()
            )

            physiology = (
                self.physiology_service.build(
                    athlete_profile_id=(
                        athlete_profile_id
                    ),
                    athlete=athlete,
                    reference_date=adapted.date,
                )
            )

            prescription = (
                build_continuous_session_prescription(
                    stimulus=stimulus,
                    duration_minutes=(
                        adapted.duration_minutes
                    ),
                    physiology=physiology,
                )
            )

            return replace(
                adapted,
                prescription=prescription,
            )

        # ------------------------------------------------------
        # Même stimulus, durée modifiée
        # ------------------------------------------------------

        if (
            adapted.duration_minutes
            != original.duration_minutes
        ):
            prescription = adapted.prescription

            if not isinstance(
                prescription,
                dict,
            ):
                raise DailyAdaptationApplicationError(
                    "La séance adaptée ne possède "
                    "pas de prescription structurée."
                )

            work_structure = (
                prescription.get(
                    "work_structure"
                )
            )

            if not isinstance(
                work_structure,
                dict,
            ):
                raise DailyAdaptationApplicationError(
                    "La structure de travail de la "
                    "séance est absente."
                )

            if (
                work_structure.get("type")
                != "continuous"
            ):
                raise DailyAdaptationApplicationError(
                    "Une réduction de durée automatique "
                    "n'est actuellement supportée que "
                    "pour les séances continues."
                )

            updated_structure = {
                **work_structure,
                "available_minutes": (
                    adapted.duration_minutes
                ),
                "continuous_minutes": (
                    adapted.duration_minutes
                ),
            }

            updated_prescription = {
                **prescription,
                "work_structure": (
                    updated_structure
                ),
            }

            return replace(
                adapted,
                prescription=(
                    updated_prescription
                ),
            )

        return adapted
