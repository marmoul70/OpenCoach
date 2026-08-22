from dataclasses import dataclass
from typing import Literal

from .season_policy import (
    PolicyAuthority,
    SeasonPolicyRule,
)


PolicyEvaluationStatus = Literal[
    "passed",
    "violated",
    "not_applicable",
    "unevaluable",
]


@dataclass(frozen=True)
class PolicyRuleEvaluation:
    """Résultat de l'évaluation d'une règle de policy."""

    rule_id: str

    authority: PolicyAuthority

    status: PolicyEvaluationStatus

    message: str

    observed_value: float | None = None
    limit_value: float | None = None

    @property
    def unevaluable(self) -> bool:
        return self.status == "unevaluable"

    @property
    def violated(self) -> bool:
        return self.status == "violated"


@dataclass(frozen=True)
class SeasonPolicyEvaluation:
    """Résultat global de l'évaluation d'une policy."""

    evaluations: tuple[
        PolicyRuleEvaluation,
        ...
    ]

    @property
    def violations(
        self,
    ) -> tuple[PolicyRuleEvaluation, ...]:
        return tuple(
            evaluation
            for evaluation in self.evaluations
            if evaluation.violated
        )

    @property
    def hard_violations(
        self,
    ) -> tuple[PolicyRuleEvaluation, ...]:
        return tuple(
            evaluation
            for evaluation in self.violations
            if evaluation.authority == "hard_limit"
        )

    @property
    def warning_violations(
        self,
    ) -> tuple[PolicyRuleEvaluation, ...]:
        return tuple(
            evaluation
            for evaluation in self.violations
            if evaluation.authority == "warning"
        )

    @property
    def acceptable(self) -> bool:
        """Une hard limit violée ou non évaluable bloque la proposition."""

        return not (
            self.hard_violations
            or self.unevaluable_hard_limits
    )

    @property
    def unevaluable_hard_limits(
        self,
    ) -> tuple[PolicyRuleEvaluation, ...]:
        return tuple(
            evaluation
            for evaluation in self.evaluations
            if (
                evaluation.authority == "hard_limit"
                and evaluation.unevaluable
            )
        )
