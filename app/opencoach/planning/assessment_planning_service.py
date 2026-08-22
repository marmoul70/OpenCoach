from datetime import date

from opencoach.models import (
    TrainingSession,
)

from .assessment_placement_apply import (
    AssessmentPlacementApplication,
    apply_assessment_placement,
)
from .assessment_placement_proposal import (
    AssessmentPlacementProposal,
    build_assessment_placement_proposal,
)
from .assessment_recommendation import (
    AssessmentPlanRecommendation,
)
from .assessment_session import (
    build_assessment_session_spec,
)
from .assessment_session_placement import (
    place_assessment_session,
)
from .weekly_availability import (
    WeeklyAvailability,
)


class AssessmentPlanningError(
    RuntimeError
):
    """Erreur d'orchestration de la planification d'une calibration."""


class AssessmentPlanningService:
    """Orchestre la proposition et l'application d'une calibration."""

    def propose(
        self,
        *,
        recommendation: AssessmentPlanRecommendation,
        target_date: date,
        week: WeeklyAvailability,
        existing_sessions: tuple[
            TrainingSession,
            ...
        ] = (),
    ) -> AssessmentPlacementProposal:
        """Construit une proposition de placement explicable."""

        spec = build_assessment_session_spec(
            recommendation
        )

        if spec is None:
            raise AssessmentPlanningError(
                "La recommandation ne peut pas être planifiée."
            )

        placement = place_assessment_session(
            spec=spec,
            target_date=target_date,
            week=week,
            existing_sessions=existing_sessions,
        )

        return build_assessment_placement_proposal(
            spec=spec,
            target_date=target_date,
            placement=placement,
        )

    def apply(
        self,
        *,
        proposal: AssessmentPlacementProposal,
        confirmed: bool = False,
    ) -> AssessmentPlacementApplication:
        """Applique une proposition autorisée ou confirmée."""

        return apply_assessment_placement(
            proposal=proposal,
            confirmed=confirmed,
        )
