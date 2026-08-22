from datetime import date

import pytest

from opencoach.planning import (
    PolicySource,
    RelativeLoadLimitParameters,
    SeasonPlanningPolicy,
    SeasonPolicyRule,
)


def create_source():
    return PolicySource(
        source_id="source-001",
        source_type="scientific_review",
        title="Evidence review",
        reference="doi:test",
        publication_year=2027,
    )


def create_rule(
    *,
    rule_id="load-progression-001",
    category="load_progression",
    authority="warning",
    enabled=True,
):
    return SeasonPolicyRule(
        rule_id=rule_id,
        category=category,
        authority=authority,
        description=(
            "Limiter les progressions trop agressives."
        ),
        rationale=(
            "Réduire le risque de surcharge."
        ),
        sources=(
            create_source(),
        ),
        enabled=enabled,
    )


def create_policy(
    *,
    rules=None,
):
    if rules is None:
        rules = (
            create_rule(),
        )

    return SeasonPlanningPolicy(
        policy_id="season-planning",
        version="1.0",
        effective_from=date(
            2027,
            1,
            1,
        ),
        rules=tuple(rules),
        description=(
            "Policy stratégique OpenCoach."
        ),
    )


def test_policy_exposes_versioned_identity() -> None:
    policy = create_policy()

    assert (
        policy.policy_id
        == "season-planning"
    )

    assert policy.version == "1.0"

    assert (
        policy.effective_from
        == date(
            2027,
            1,
            1,
        )
    )


def test_policy_distinguishes_authority_levels() -> None:
    policy = create_policy(
        rules=(
            create_rule(
                rule_id="advisory",
                authority="advisory",
            ),
            create_rule(
                rule_id="warning",
                authority="warning",
            ),
            create_rule(
                rule_id="hard",
                authority="hard_limit",
            ),
        )
    )

    assert len(
        policy.rules_by_authority(
            "advisory"
        )
    ) == 1

    assert len(
        policy.rules_by_authority(
            "warning"
        )
    ) == 1

    assert len(
        policy.rules_by_authority(
            "hard_limit"
        )
    ) == 1


def test_policy_filters_disabled_rules() -> None:
    policy = create_policy(
        rules=(
            create_rule(
                rule_id="enabled",
            ),
            create_rule(
                rule_id="disabled",
                enabled=False,
            ),
        )
    )

    assert len(
        policy.enabled_rules
    ) == 1

    assert (
        policy.enabled_rules[0].rule_id
        == "enabled"
    )


def test_policy_can_filter_by_category() -> None:
    policy = create_policy(
        rules=(
            create_rule(
                rule_id="load",
                category="load_progression",
            ),
            create_rule(
                rule_id="taper",
                category="taper",
            ),
        )
    )

    taper_rules = (
        policy.rules_by_category(
            "taper"
        )
    )

    assert len(
        taper_rules
    ) == 1

    assert (
        taper_rules[0].rule_id
        == "taper"
    )


def test_policy_can_find_rule_by_id() -> None:
    policy = create_policy()

    rule = policy.get_rule(
        "load-progression-001"
    )

    assert rule is not None

    assert (
        rule.category
        == "load_progression"
    )


def test_unknown_rule_returns_none() -> None:
    policy = create_policy()

    assert policy.get_rule(
        "unknown"
    ) is None


def test_duplicate_rule_ids_are_rejected() -> None:
    rule = create_rule()

    with pytest.raises(
        ValueError,
        match="uniques",
    ):
        create_policy(
            rules=(
                rule,
                rule,
            )
        )


def test_policy_source_requires_identity() -> None:
    with pytest.raises(
        ValueError,
        match="source",
    ):
        PolicySource(
            source_id="",
            source_type="scientific_review",
            title="Source",
        )


def test_policy_rule_requires_rationale() -> None:
    with pytest.raises(
        ValueError,
        match="justifiée",
    ):
        SeasonPolicyRule(
            rule_id="test",
            category="other",
            authority="advisory",
            description="Test.",
            rationale="",
            sources=(),
        )

def test_policy_rule_can_carry_typed_parameters() -> None:
    rule = SeasonPolicyRule(
        rule_id="load-relative",
        category="load_progression",
        authority="warning",
        description="Contrôler la progression.",
        rationale="Éviter une progression excessive.",
        sources=(
            create_source(),
        ),
        parameters=RelativeLoadLimitParameters(
            reference="baseline",
            max_multiplier=1.15,
        ),
    )

    assert isinstance(
        rule.parameters,
        RelativeLoadLimitParameters,
    )

    assert (
        rule.parameters.max_multiplier
        == 1.15
    )
