from opencoach.planning import (
    PolicyRuleEvaluation,
    SeasonPolicyEvaluation,
    SeasonStrategyGateResult,
    SeasonStrategyValidation,
    StrategyViolation,
)

from opencoach.planning.season_strategy_gate import (
    _build_gate_reasons,
    _resolve_gate_status,
)


def structural(
    *violations,
):
    return SeasonStrategyValidation(
        violations=tuple(violations),
    )


def policy(
    *evaluations,
):
    return SeasonPolicyEvaluation(
        evaluations=tuple(evaluations),
    )


def test_clean_proposal_is_accepted() -> None:
    status = _resolve_gate_status(
        structural_validation=structural(),
        policy_evaluation=policy(),
    )

    assert status == "accept"


def test_warning_produces_accept_with_warnings() -> None:
    status = _resolve_gate_status(
        structural_validation=structural(),
        policy_evaluation=policy(
            PolicyRuleEvaluation(
                rule_id="load-warning",
                authority="warning",
                status="violated",
                message="Progression élevée.",
            )
        ),
    )

    assert status == "accept_with_warnings"


def test_structural_warning_produces_accept_with_warnings() -> None:
    status = _resolve_gate_status(
        structural_validation=structural(
            StrategyViolation(
                rule_id="soft-rule",
                severity="warning",
                message="Point à surveiller.",
            )
        ),
        policy_evaluation=policy(),
    )

    assert status == "accept_with_warnings"


def test_hard_policy_violation_requires_revision() -> None:
    status = _resolve_gate_status(
        structural_validation=structural(),
        policy_evaluation=policy(
            PolicyRuleEvaluation(
                rule_id="hard-load-limit",
                authority="hard_limit",
                status="violated",
                message="Limite dépassée.",
            )
        ),
    )

    assert status == "revise"


def test_structural_error_requires_revision() -> None:
    status = _resolve_gate_status(
        structural_validation=structural(
            StrategyViolation(
                rule_id="week-overlap",
                severity="error",
                message="Semaines superposées.",
            )
        ),
        policy_evaluation=policy(),
    )

    assert status == "revise"


def test_structural_error_has_priority_over_warning() -> None:
    status = _resolve_gate_status(
        structural_validation=structural(
            StrategyViolation(
                rule_id="invalid-phase",
                severity="error",
                message="Phase invalide.",
            )
        ),
        policy_evaluation=policy(
            PolicyRuleEvaluation(
                rule_id="warning",
                authority="warning",
                status="violated",
                message="Warning.",
            )
        ),
    )

    assert status == "revise"


def test_gate_reasons_are_explainable() -> None:
    reasons = _build_gate_reasons(
        structural_validation=structural(
            StrategyViolation(
                rule_id="week-overlap",
                severity="error",
                message="Semaines superposées.",
            )
        ),
        policy_evaluation=policy(
            PolicyRuleEvaluation(
                rule_id="load-limit",
                authority="warning",
                status="violated",
                message="Charge élevée.",
            )
        ),
    )

    assert (
        "week-overlap: Semaines superposées."
        in reasons
    )

    assert (
        "load-limit: Charge élevée."
        in reasons
    )


def test_gate_result_exposes_state_helpers() -> None:
    result = SeasonStrategyGateResult(
        status="accept_with_warnings",
        structural_validation=structural(),
        policy_evaluation=policy(),
        reasons=(),
    )

    assert result.accepted is True
    assert result.requires_revision is False
    assert result.rejected is False


def test_revision_state_is_not_accepted() -> None:
    result = SeasonStrategyGateResult(
        status="revise",
        structural_validation=structural(),
        policy_evaluation=policy(),
        reasons=(),
    )

    assert result.accepted is False
    assert result.requires_revision is True
    assert result.rejected is False


def test_reject_state_is_exposed() -> None:
    result = SeasonStrategyGateResult(
        status="reject",
        structural_validation=structural(),
        policy_evaluation=policy(),
        reasons=(),
    )

    assert result.accepted is False
    assert result.requires_revision is False
    assert result.rejected is True
