from .policy_evaluation import (
    SeasonPolicyEvaluation,
)
from .policy_evaluators import (
    evaluate_policy_rule,
)
from .season_planning_input import (
    SeasonPlanningInput,
)
from .season_policy import (
    SeasonPlanningPolicy,
)
from .season_strategy_proposal import (
    SeasonStrategyProposal,
)


def evaluate_season_policy(
    *,
    planning_input: SeasonPlanningInput,
    proposal: SeasonStrategyProposal,
    policy: SeasonPlanningPolicy,
) -> SeasonPolicyEvaluation:
    """Évalue toutes les règles actives d'une policy."""

    evaluations = tuple(
        evaluate_policy_rule(
            planning_input=planning_input,
            proposal=proposal,
            rule=rule,
        )
        for rule in policy.enabled_rules
    )

    return SeasonPolicyEvaluation(
        evaluations=evaluations,
    )
