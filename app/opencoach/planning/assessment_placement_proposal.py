from dataclasses import dataclass
from datetime import date
from typing import Literal

from .assessment_session import (
    AssessmentSessionSpec,
)
from .placement_result import (
    SessionPlacementResult,
)


AssessmentPlacementStatus = Literal[
    "proposed",
    "confirmation_required",
    "no_solution",
]


@dataclass(frozen=True)
class AssessmentPlacementProposal:
    """Proposition explicable de placement d'une calibration."""

    status: AssessmentPlacementStatus

    spec: AssessmentSessionSpec

    target_date: date
    proposed_date: date | None

    requires_confirmation: bool

    reasons: tuple[str, ...]

    rejected_reasons: tuple[str, ...]

    @property
    def has_solution(self) -> bool:
        return self.proposed_date is not None

    @property
    def can_be_applied_directly(self) -> bool:
        return (
            self.status == "proposed"
            and self.proposed_date is not None
            and not self.requires_confirmation
        )


def build_assessment_placement_proposal(
    *,
    spec: AssessmentSessionSpec,
    target_date: date,
    placement: SessionPlacementResult,
) -> AssessmentPlacementProposal:
    """Transforme le résultat du moteur en proposition métier."""

    best = placement.best_candidate

    if best is None:
        return AssessmentPlacementProposal(
            status="no_solution",
            spec=spec,
            target_date=target_date,
            proposed_date=None,
            requires_confirmation=False,
            reasons=(
                "Aucun jour compatible n'a été trouvé "
                "pour cette séance de calibration.",
            ),
            rejected_reasons=_collect_rejected_reasons(
                placement
            ),
        )

    requires_confirmation = (
        best.requires_confirmation
    )

    status: AssessmentPlacementStatus = (
        "confirmation_required"
        if requires_confirmation
        else "proposed"
    )

    reasons = list(
        best.reasons
    )

    if best.date == target_date:
        reasons.insert(
            0,
            "La séance peut être conservée à la date cible.",
        )
    else:
        reasons.insert(
            0,
            "La séance doit être placée à une date alternative.",
        )

    if requires_confirmation:
        reasons.append(
            "Ce jour nécessite la confirmation de l'athlète."
        )

    return AssessmentPlacementProposal(
        status=status,
        spec=spec,
        target_date=target_date,
        proposed_date=best.date,
        requires_confirmation=requires_confirmation,
        reasons=tuple(reasons),
        rejected_reasons=_collect_rejected_reasons(
            placement
        ),
    )


def _collect_rejected_reasons(
    placement: SessionPlacementResult,
) -> tuple[str, ...]:
    reasons: list[str] = []

    for candidate in placement.rejected_candidates:
        for rule in candidate.rules:
            if (
                rule.violated
                and rule.reason not in reasons
            ):
                reasons.append(
                    rule.reason
                )

    return tuple(reasons)
