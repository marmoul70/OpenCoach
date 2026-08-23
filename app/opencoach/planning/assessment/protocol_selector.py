from dataclasses import dataclass

from opencoach.planning.assessment.need import (
    AssessmentNeed,
)
from opencoach.planning.assessment.protocol import (
    AssessmentProtocol,
    get_assessment_protocols,
)
from opencoach.planning.assessment.safety import (
    AssessmentSafetyContext,
)

@dataclass(frozen=True)
class AssessmentSelectionContext:
    """Contexte déterministe utilisé pour sélectionner un protocole."""

    maximal_testing_allowed: bool = True

    track_available: bool = False
    flat_route_available: bool = True
    laboratory_available: bool = False


@dataclass(frozen=True)
class AssessmentProtocolCandidate:
    """Protocole évalué pour un besoin donné."""

    protocol: AssessmentProtocol

    eligible: bool
    score: int

    reasons: tuple[str, ...]


@dataclass(frozen=True)
class AssessmentProtocolSelection:
    """Résultat du classement des protocoles de calibration."""

    candidates: tuple[
        AssessmentProtocolCandidate,
        ...
    ]

    @property
    def eligible_candidates(
        self,
    ) -> tuple[AssessmentProtocolCandidate, ...]:
        return tuple(
            candidate
            for candidate in self.candidates
            if candidate.eligible
        )

    @property
    def rejected_candidates(
        self,
    ) -> tuple[AssessmentProtocolCandidate, ...]:
        return tuple(
            candidate
            for candidate in self.candidates
            if not candidate.eligible
        )

    @property
    def best_candidate(
        self,
    ) -> AssessmentProtocolCandidate | None:
        if not self.eligible_candidates:
            return None

        return self.eligible_candidates[0]

    @property
    def has_solution(self) -> bool:
        return self.best_candidate is not None


def select_assessment_protocol(
    *,
    need: AssessmentNeed,
    context: AssessmentSelectionContext,
) -> AssessmentProtocolSelection:
    """Classe les protocoles compatibles avec un besoin de calibration."""

    protocols = get_assessment_protocols(
        need.assessment_type
    )

    candidates = tuple(
        _evaluate_protocol(
            need=need,
            protocol=protocol,
            context=context,
        )
        for protocol in protocols
    )

    ordered = tuple(
        sorted(
            candidates,
            key=lambda candidate: (
                not candidate.eligible,
                -candidate.score,
                candidate.protocol.protocol_id,
            ),
        )
    )

    return AssessmentProtocolSelection(
        candidates=ordered,
    )


def _evaluate_protocol(
    *,
    need: AssessmentNeed,
    protocol: AssessmentProtocol,
    context: AssessmentSelectionContext,
) -> AssessmentProtocolCandidate:
    score = 100
    reasons: list[str] = []

    eligible = True

    required_metrics = set(
        need.metrics
    )

    covered_metrics = set(
        protocol.metrics
    )

    missing_metrics = (
        required_metrics
        - covered_metrics
    )

    if missing_metrics:
        eligible = False

        reasons.append(
            "Le protocole ne couvre pas toutes les "
            "métriques demandées."
        )

    if (
        protocol.intensity == "maximal"
        and not context.maximal_testing_allowed
    ):
        eligible = False

        reasons.append(
            "Les tests maximaux ne sont pas autorisés actuellement."
        )

    if protocol.environment == "track":
        if context.track_available:
            score += 20

            reasons.append(
                "Une piste est disponible."
            )

        else:
            eligible = False

            reasons.append(
                "Ce protocole nécessite une piste disponible."
            )

    elif protocol.environment == "flat":
        if context.flat_route_available:
            score += 10

            reasons.append(
                "Un terrain plat adapté est disponible."
            )

        else:
            eligible = False

            reasons.append(
                "Ce protocole nécessite un terrain plat adapté."
            )

    elif protocol.environment == "laboratory":
        if context.laboratory_available:
            score += 15

            reasons.append(
                "Un laboratoire est disponible."
            )

        else:
            eligible = False

            reasons.append(
                "Ce protocole nécessite un laboratoire."
            )

    if protocol.requires_external_equipment:
        score -= 5

        reasons.append(
            "Le protocole nécessite des moyens externes."
        )

    return AssessmentProtocolCandidate(
        protocol=protocol,
        eligible=eligible,
        score=score,
        reasons=tuple(reasons),
    )

def build_assessment_selection_context(
    *,
    safety: AssessmentSafetyContext,
    track_available: bool = False,
    flat_route_available: bool = True,
    laboratory_available: bool = False,
) -> AssessmentSelectionContext:
    """Construit le contexte du selector à partir des garde-fous réels."""

    return AssessmentSelectionContext(
        maximal_testing_allowed=(
            safety.maximal_testing_allowed
        ),
        track_available=track_available,
        flat_route_available=flat_route_available,
        laboratory_available=laboratory_available,
    )