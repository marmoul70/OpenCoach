from collections.abc import Callable

from .policy_evaluation import (
    PolicyRuleEvaluation,
)
from .policy_parameters import (
    PolicyParameters,
    RelativeLoadLimitParameters,
)
from .season_planning_input import (
    SeasonPlanningInput,
)
from .season_policy import (
    SeasonPolicyRule,
)
from .season_strategy_proposal import (
    SeasonStrategyProposal,
)


PolicyEvaluator = Callable[
    [
        SeasonPlanningInput,
        SeasonStrategyProposal,
        SeasonPolicyRule,
    ],
    PolicyRuleEvaluation,
]


def evaluate_policy_rule(
    *,
    planning_input: SeasonPlanningInput,
    proposal: SeasonStrategyProposal,
    rule: SeasonPolicyRule,
) -> PolicyRuleEvaluation:
    """Route une règle vers son évaluateur typé."""

    parameters = rule.parameters

    if parameters is None:
        return PolicyRuleEvaluation(
            rule_id=rule.rule_id,
            authority=rule.authority,
            status=(
                "unevaluable"
                if rule.authority == "hard_limit"
                else "not_applicable"
            ),
            message=(
                "La hard limit ne contient aucun paramètre "
                "permettant son évaluation."
                if rule.authority == "hard_limit"
                else (
                    "La règle ne contient aucun "
                    "paramètre évaluateur."
                )
            ),
        )

    evaluator = _EVALUATORS.get(
        type(parameters)
    )

    if evaluator is None:
        return PolicyRuleEvaluation(
            rule_id=rule.rule_id,
            authority=rule.authority,
            status=(
                "unevaluable"
                if rule.authority == "hard_limit"
                else "not_applicable"
            ),
            message=(
                "Aucun évaluateur n'est disponible "
                "pour cette hard limit."
                if rule.authority == "hard_limit"
                else (
                    "Aucun évaluateur n'est disponible "
                    "pour ce type de paramètres."
                )
            ),
        )

    return evaluator(
        planning_input,
        proposal,
        rule,
    )


def _evaluate_relative_load_limit(
    planning_input: SeasonPlanningInput,
    proposal: SeasonStrategyProposal,
    rule: SeasonPolicyRule,
) -> PolicyRuleEvaluation:
    parameters = rule.parameters

    assert isinstance(
        parameters,
        RelativeLoadLimitParameters,
    )

    reference_value = _resolve_load_reference(
        planning_input=planning_input,
        parameters=parameters,
    )

    if reference_value is None:
        return PolicyRuleEvaluation(
            rule_id=rule.rule_id,
            authority=rule.authority,
            status=(
                "unevaluable"
                if rule.authority == "hard_limit"
                else "not_applicable"
            ),
            message=(
                "La référence de charge nécessaire "
                "à cette règle n'est pas disponible."
            ),
        )

    target_loads = tuple(
        week.target_load
        for week in proposal.weeks
        if week.target_load is not None
    )

    if not target_loads:
        return PolicyRuleEvaluation(
            rule_id=rule.rule_id,
            authority=rule.authority,
            status=(
                "unevaluable"
                if rule.authority == "hard_limit"
                else "not_applicable"
            ),
            message=(
                "La proposition ne contient aucune "
                "charge hebdomadaire cible."
            ),
        )

    observed = max(
        target_loads
    )

    limit = (
        reference_value
        * parameters.max_multiplier
    )

    violated = observed > limit

    return PolicyRuleEvaluation(
        rule_id=rule.rule_id,
        authority=rule.authority,
        status=(
            "violated"
            if violated
            else "passed"
        ),
        message=(
            "La charge maximale proposée dépasse "
            "la limite relative autorisée."
            if violated
            else (
                "La charge maximale proposée reste "
                "dans la limite relative."
            )
        ),
        observed_value=round(
            observed,
            2,
        ),
        limit_value=round(
            limit,
            2,
        ),
    )


def _resolve_load_reference(
    *,
    planning_input: SeasonPlanningInput,
    parameters: RelativeLoadLimitParameters,
) -> float | None:
    if parameters.reference == "baseline":
        return (
            planning_input
            .athlete
            .baseline
            .weekly_training_load
        )

    if parameters.reference == "recent_average":
        recent_stats = (
            planning_input
            .training_state
            .recent_stats
        )

        if recent_stats is None:
            return None

        training_load = getattr(
            recent_stats,
            "training_load",
            None,
        )

        if training_load is None:
            return None

        return float(
            training_load
        )

    if parameters.reference == "previous_week":
        previous_strategy = (
            planning_input.previous_strategy
        )

        if previous_strategy is None:
            return None

        past_weeks = tuple(
            week
            for week in previous_strategy.weeks
            if (
                week.end_date
                < planning_input.planning_date
                and week.target_load is not None
            )
        )

        if not past_weeks:
            return None

        latest = max(
            past_weeks,
            key=lambda week: week.end_date,
        )

        return latest.target_load

    return None


_EVALUATORS: dict[
    type[PolicyParameters],
    PolicyEvaluator,
] = {
    RelativeLoadLimitParameters: (
        _evaluate_relative_load_limit
    ),
}
