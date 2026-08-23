from dataclasses import dataclass
from typing import Literal

from opencoach.planning.assessment.need import (
    AssessmentNeed,
)
from opencoach.planning.assessment.protocol import (
    AssessmentProtocol,
)
from opencoach.planning.assessment.protocol_selector import (
    AssessmentProtocolSelection,
)
from opencoach.planning.assessment.safety import (
    AssessmentSafetyContext,
)


AssessmentRecommendationStatus = Literal[
    "ready_to_schedule",
    "deferred",
    "no_protocol_available",
]


@dataclass(frozen=True)
class AssessmentPlanRecommendation:
    """Décision métier concernant un besoin de calibration."""

    need: AssessmentNeed

    status: AssessmentRecommendationStatus

    protocol: AssessmentProtocol | None

    safety: AssessmentSafetyContext

    reasons: tuple[str, ...]

    @property
    def ready_to_schedule(self) -> bool:
        return (
            self.status
            == "ready_to_schedule"
        )


def build_assessment_recommendation(
    *,
    need: AssessmentNeed,
    safety: AssessmentSafetyContext,
    selection: AssessmentProtocolSelection,
) -> AssessmentPlanRecommendation:
    """Construit la recommandation finale d'un besoin de calibration."""

    best_candidate = selection.best_candidate

    if best_candidate is None:
        if safety.has_blockers:
            return AssessmentPlanRecommendation(
                need=need,
                status="deferred",
                protocol=None,
                safety=safety,
                reasons=safety.blocking_reasons,
            )

        reasons = tuple(
            reason
            for candidate in selection.rejected_candidates
            for reason in candidate.reasons
        )

        if not reasons:
            reasons = (
                "Aucun protocole compatible n'est actuellement disponible.",
            )

        return AssessmentPlanRecommendation(
            need=need,
            status="no_protocol_available",
            protocol=None,
            safety=safety,
            reasons=reasons,
        )

    return AssessmentPlanRecommendation(
        need=need,
        status="ready_to_schedule",
        protocol=best_candidate.protocol,
        safety=safety,
        reasons=best_candidate.reasons,
    )