from dataclasses import dataclass

from opencoach.models import (
    TrainingSession,
)

from opencoach.planning.assessment.placement_proposal import (
    AssessmentPlacementProposal,
)
from opencoach.planning.assessment.session_placement import (
    build_assessment_training_session,
)


class AssessmentPlacementApplyError(
    RuntimeError
):
    """Erreur lors de l'application d'une proposition de calibration."""


@dataclass(frozen=True)
class AssessmentPlacementApplication:
    """Résultat de l'application d'une proposition validée."""

    proposal: AssessmentPlacementProposal
    session: TrainingSession

    athlete_confirmation_used: bool


def apply_assessment_placement(
    *,
    proposal: AssessmentPlacementProposal,
    confirmed: bool = False,
) -> AssessmentPlacementApplication:
    """Matérialise une proposition de placement autorisée."""

    if not proposal.has_solution:
        raise AssessmentPlacementApplyError(
            "Impossible d'appliquer une proposition sans solution."
        )

    if proposal.proposed_date is None:
        raise AssessmentPlacementApplyError(
            "La proposition ne contient aucune date exploitable."
        )

    if (
        proposal.requires_confirmation
        and not confirmed
    ):
        raise AssessmentPlacementApplyError(
            "La confirmation de l'athlète est requise "
            "avant d'appliquer cette proposition."
        )

    session = build_assessment_training_session(
        spec=proposal.spec,
        session_date=proposal.proposed_date,
    )

    return AssessmentPlacementApplication(
        proposal=proposal,
        session=session,
        athlete_confirmation_used=(
            proposal.requires_confirmation
            and confirmed
        ),
    )
