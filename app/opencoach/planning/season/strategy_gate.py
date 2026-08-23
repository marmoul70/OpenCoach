from dataclasses import dataclass
from typing import Literal

from opencoach.planning.season.policy_evaluation import (
    SeasonPolicyEvaluation,
)
from opencoach.planning.season.planning_input import (
    SeasonPlanningInput,
)
from opencoach.planning.season.policy import (
    SeasonPlanningPolicy,
)
from opencoach.planning.season.policy_evaluator import (
    evaluate_season_policy,
)
from opencoach.planning.season.strategy_proposal import (
    SeasonStrategyProposal,
)
from opencoach.planning.season.strategy_validator import (
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

    contract_reasons = _validate_policy_contract(
        planning_input=planning_input,
        policy=policy,
    )

    if contract_reasons:
        return SeasonStrategyGateResult(
            status="reject",
            structural_validation=SeasonStrategyValidation(
                violations=(),
            ),
            policy_evaluation=SeasonPolicyEvaluation(
                evaluations=(),
            ),
            reasons=contract_reasons,
        )

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


def _validate_policy_contract(
    *,
    planning_input: SeasonPlanningInput,
    policy: SeasonPlanningPolicy,
) -> tuple[str, ...]:
    """Vérifie que la bonne policy est utilisée à la bonne date."""

    reasons: list[str] = []

    if (
        planning_input.knowledge.policy_id
        != policy.policy_id
    ):
        reasons.append(
            "policy_id_mismatch: "
            "La policy fournie ne correspond pas "
            "à celle déclarée dans SeasonPlanningInput."
        )

    if (
        planning_input.knowledge.policy_version
        != policy.version
    ):
        reasons.append(
            "policy_version_mismatch: "
            "La version de policy fournie ne correspond pas "
            "à celle déclarée dans SeasonPlanningInput."
        )

    if (
        policy.effective_from
        > planning_input.planning_date
    ):
        reasons.append(
            "policy_not_effective_yet: "
            "La policy n'est pas encore applicable "
            "à la date de planification."
        )

    return tuple(reasons)


def _resolve_gate_status(
    *,
    structural_validation: SeasonStrategyValidation,
    policy_evaluation: SeasonPolicyEvaluation,
) -> SeasonStrategyGateStatus:
    """Détermine l'état final du Gate."""

    if structural_validation.errors:
        return "revise"

    if policy_evaluation.unevaluable_hard_limits:
        return "reject"

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
    """Construit des raisons exploitables par l'IA et les logs."""

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

    reasons.extend(
        (
            f"{evaluation.rule_id}: "
            f"{evaluation.message}"
        )
        for evaluation
        in policy_evaluation.unevaluable_hard_limits
    )

    return tuple(reasons)