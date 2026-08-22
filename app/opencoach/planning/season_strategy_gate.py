from dataclasses import dataclass
from typing import Literal

from .policy_evaluation import (
    SeasonPolicyEvaluation,
)
from .season_planning_input import (
    SeasonPlanningInput,
)
from .season_policy import (
    SeasonPlanningPolicy,
)
from .season_policy_evaluator import (
    evaluate_season_policy,
)
from .season_strategy_proposal import (
    SeasonStrategyProposal,
)
from .season_strategy_validator import (
    SeasonStrategyValidation,
    validate_season_strategy_proposal,
)


SeasonStrategyGateStatus = Literal[
    "accept",
    "accept_with_warnings",
    "revise",
    "reject",
]


@dataclass(frozen=True)
class SeasonStrategyGateResult:
    """Décision finale sur une proposition stratégique IA."""

    status: SeasonStrategyGateStatus

    structural_validation: SeasonStrategyValidation

    policy_evaluation: SeasonPolicyEvaluation

    reasons: tuple[
        str,
        ...
    ]

    @property
    def accepted(self) -> bool:
        return self.status in {
            "accept",
            "accept_with_warnings",
        }

    @property
    def requires_revision(self) -> bool:
        return self.status == "revise"

    @property
    def rejected(self) -> bool:
        return self.status == "reject"


def evaluate_season_strategy_gate(
    *,
    planning_input: SeasonPlanningInput,
    proposal: SeasonStrategyProposal,
    policy: SeasonPlanningPolicy,
) -> SeasonStrategyGateResult:
    """Applique tous les garde-fous Python à une proposition IA."""

    structural_validation = (
        validate_season_strategy_proposal(
            planning_input=planning_input,
            proposal=proposal,
        )
    )

    policy_evaluation = (
        evaluate_season_policy(
            planning_input=planning_input,
            proposal=proposal,
            policy=policy,
        )
    )

    status = _resolve_gate_status(
        structural_validation=structural_validation,
        policy_evaluation=policy_evaluation,
    )

    reasons = _build_gate_reasons(
        structural_validation=structural_validation,
        policy_evaluation=policy_evaluation,
    )

    return SeasonStrategyGateResult(
        status=status,
        structural_validation=structural_validation,
        policy_evaluation=policy_evaluation,
        reasons=reasons,
    )


def _resolve_gate_status(
    *,
    structural_validation: SeasonStrategyValidation,
    policy_evaluation: SeasonPolicyEvaluation,
) -> SeasonStrategyGateStatus:
    if structural_validation.errors:
        return "revise"

    if policy_evaluation.hard_violations:
        return "revise"

    if (
        structural_validation.warnings
        or policy_evaluation.warning_violations
    ):
        return "accept_with_warnings"

    return "accept"


def _build_gate_reasons(
    *,
    structural_validation: SeasonStrategyValidation,
    policy_evaluation: SeasonPolicyEvaluation,
) -> tuple[str, ...]:
    reasons: list[str] = []

    reasons.extend(
        (
            f"{violation.rule_id}: "
            f"{violation.message}"
        )
        for violation
        in structural_validation.violations
    )

    reasons.extend(
        (
            f"{evaluation.rule_id}: "
            f"{evaluation.message}"
        )
        for evaluation
        in policy_evaluation.violations
    )

    return tuple(reasons)
