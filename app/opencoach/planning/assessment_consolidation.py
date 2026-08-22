from dataclasses import dataclass

from .assessment_need import (
    AssessmentNeed,
    AssessmentPriority,
)
from .assessment_protocol import (
    ASSESSMENT_PROTOCOLS,
    AssessmentProtocol,
)


@dataclass(frozen=True)
class ConsolidatedAssessmentPlan:
    """Plan de calibration consolidant un ou plusieurs besoins."""

    protocol: AssessmentProtocol

    needs: tuple[
        AssessmentNeed,
        ...
    ]

    priority: AssessmentPriority

    covered_metrics: tuple[str, ...]

    @property
    def assessment_types(
        self,
    ) -> tuple[str, ...]:
        return tuple(
            need.assessment_type
            for need in self.needs
        )


def consolidate_assessment_needs(
    needs: tuple[
        AssessmentNeed,
        ...
    ],
) -> tuple[
    ConsolidatedAssessmentPlan,
    ...,
]:
    """Regroupe les besoins pouvant être couverts par un même protocole."""

    remaining = list(
        needs
    )

    plans: list[
        ConsolidatedAssessmentPlan
    ] = []

    while remaining:
        protocol, covered = _find_best_protocol(
            tuple(remaining)
        )

        if (
            protocol is None
            or not covered
        ):
            break

        plan = ConsolidatedAssessmentPlan(
            protocol=protocol,
            needs=covered,
            priority=_highest_priority(
                covered
            ),
            covered_metrics=_covered_metrics(
                covered
            ),
        )

        plans.append(
            plan
        )

        covered_ids = {
            id(need)
            for need in covered
        }

        remaining = [
            need
            for need in remaining
            if id(need)
            not in covered_ids
        ]

    return tuple(
        plans
    )


def _find_best_protocol(
    needs: tuple[
        AssessmentNeed,
        ...
    ],
) -> tuple[
    AssessmentProtocol | None,
    tuple[AssessmentNeed, ...],
]:
    best_protocol: AssessmentProtocol | None = None
    best_needs: tuple[
        AssessmentNeed,
        ...
    ] = ()

    for protocol in ASSESSMENT_PROTOCOLS:
        covered = tuple(
            need
            for need in needs
            if _protocol_covers_need(
                protocol=protocol,
                need=need,
            )
        )

        if not covered:
            continue

        if len(covered) > len(
            best_needs
        ):
            best_protocol = protocol
            best_needs = covered

    return (
        best_protocol,
        best_needs,
    )


def _protocol_covers_need(
    *,
    protocol: AssessmentProtocol,
    need: AssessmentNeed,
) -> bool:
    if (
        need.assessment_type
        not in protocol.assessment_types
    ):
        return False

    required_metrics = set(
        need.metrics
    )

    protocol_metrics = set(
        protocol.metrics
    )

    return required_metrics.issubset(
        protocol_metrics
    )


def _highest_priority(
    needs: tuple[
        AssessmentNeed,
        ...
    ],
) -> AssessmentPriority:
    priorities = {
        need.priority
        for need in needs
    }

    if "high" in priorities:
        return "high"

    if "medium" in priorities:
        return "medium"

    return "low"


def _covered_metrics(
    needs: tuple[
        AssessmentNeed,
        ...
    ],
) -> tuple[str, ...]:
    metrics = {
        metric
        for need in needs
        for metric in need.metrics
    }

    return tuple(
        sorted(
            metrics
        )
    )
