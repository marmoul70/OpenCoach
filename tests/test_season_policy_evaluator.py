from dataclasses import replace
from datetime import date
from uuid import uuid4

from opencoach.models import (
    AthleteProfile,
    Race,
)
from opencoach.planning import (
    AthleteTrainingBaseline,
    PhysiologicalCalibrationMetric,
    PhysiologicalCalibrationSnapshot,
    PolicySource,
    RelativeLoadLimitParameters,
    SeasonAthleteContext,
    SeasonConstraintContext,
    SeasonGoalContext,
    SeasonKnowledgeContext,
    SeasonPlanningInput,
    SeasonPlanningPolicy,
    SeasonPolicyRule,
    SeasonStrategyProposal,
    SeasonTrainingState,
    TrainingStimulus,
    WeekTrajectory,
    evaluate_season_policy,
)


PLANNING_DATE = date(
    2027,
    3,
    1,
)


def missing_metric(metric):
    return PhysiologicalCalibrationMetric(
        metric=metric,
        value=None,
        source="missing",
        measurement=None,
        freshness=None,
        usable=False,
        recalibration_recommended=True,
        reason="Mesure absente.",
    )


def create_input():
    race = Race(
        id=uuid4(),
        date=date(
            2027,
            6,
            12,
        ),
        name="Objectif",
        location="Test",
        race_type="trail",
        priority="primary",
        distance_km=50.0,
        elevation_gain_m=2500.0,
        status="planned",
    )

    return SeasonPlanningInput(
        athlete_profile_id=uuid4(),
        planning_date=PLANNING_DATE,
        athlete=SeasonAthleteContext(
            profile=AthleteProfile(),
            baseline=AthleteTrainingBaseline(
                weekly_sessions=4.0,
                weekly_duration_minutes=300.0,
                weekly_distance_km=45.0,
                weekly_elevation_gain_m=1000.0,
                weekly_training_load=300.0,
                longest_duration_minutes=150.0,
                longest_distance_km=24.0,
                highest_elevation_gain_m=1400.0,
                source_confidence="high",
                reasons=(),
            ),
            physiology=PhysiologicalCalibrationSnapshot(
                vma=missing_metric("vma"),
                max_heart_rate=missing_metric(
                    "max_heart_rate"
                ),
                resting_heart_rate=missing_metric(
                    "resting_heart_rate"
                ),
                threshold_heart_rate_1=missing_metric(
                    "threshold_heart_rate_1"
                ),
                threshold_heart_rate_2=missing_metric(
                    "threshold_heart_rate_2"
                ),
            ),
        ),
        goals=SeasonGoalContext(
            target_race=race,
        ),
        training_state=SeasonTrainingState(
            recent_load=None,
            recent_stats=None,
            readiness=None,
        ),
        constraints=SeasonConstraintContext(
            constraints=(),
            known_until=date(
                2027,
                3,
                14,
            ),
        ),
        knowledge=SeasonKnowledgeContext(
            knowledge_version="2027.03",
            policy_id="season-planning",
            policy_version="1.0",
        ),
    )


def create_week(
    *,
    number,
    target_load,
):
    return WeekTrajectory(
        week_number=number,
        start_date=date(
            2027,
            3,
            1 + ((number - 1) * 7),
        ),
        end_date=date(
            2027,
            3,
            7 + ((number - 1) * 7),
        ),
        phase="build",
        target_load=target_load,
        load_min=(
            target_load - 10
        ),
        load_max=(
            target_load + 10
        ),
        target_duration_minutes=None,
        target_distance_km=None,
        target_elevation_gain_m=None,
        primary_stimuli=(
            TrainingStimulus(
                stimulus_type="aerobic_endurance",
                priority="high",
            ),
        ),
    )


def create_proposal(
    *,
    load=330.0,
):
    return SeasonStrategyProposal(
        summary="Test.",
        facts_used=(),
        assumptions=(),
        decisions=(),
        uncertainties=(),
        phases=(),
        weeks=(
            create_week(
                number=1,
                target_load=load,
            ),
        ),
    )


def create_policy(
    *,
    authority="warning",
    multiplier=1.15,
):
    source = PolicySource(
        source_id="source",
        source_type="open_coach",
        title="OpenCoach test policy",
    )

    rule = SeasonPolicyRule(
        rule_id="relative-load",
        category="load_progression",
        authority=authority,
        description=(
            "Limiter la charge par rapport à la baseline."
        ),
        rationale=(
            "Conserver une progression prudente."
        ),
        sources=(
            source,
        ),
        parameters=RelativeLoadLimitParameters(
            reference="baseline",
            max_multiplier=multiplier,
        ),
    )

    return SeasonPlanningPolicy(
        policy_id="season-planning",
        version="1.0",
        effective_from=PLANNING_DATE,
        rules=(
            rule,
        ),
    )


def test_relative_load_rule_passes():
    evaluation = evaluate_season_policy(
        planning_input=create_input(),
        proposal=create_proposal(
            load=330.0,
        ),
        policy=create_policy(
            multiplier=1.15,
        ),
    )

    assert evaluation.acceptable is True

    assert (
        evaluation.evaluations[0].status
        == "passed"
    )


def test_warning_violation_does_not_block_strategy():
    evaluation = evaluate_season_policy(
        planning_input=create_input(),
        proposal=create_proposal(
            load=380.0,
        ),
        policy=create_policy(
            authority="warning",
            multiplier=1.15,
        ),
    )

    assert evaluation.acceptable is True

    assert len(
        evaluation.warning_violations
    ) == 1


def test_hard_violation_blocks_strategy():
    evaluation = evaluate_season_policy(
        planning_input=create_input(),
        proposal=create_proposal(
            load=380.0,
        ),
        policy=create_policy(
            authority="hard_limit",
            multiplier=1.15,
        ),
    )

    assert evaluation.acceptable is False

    assert len(
        evaluation.hard_violations
    ) == 1


def test_evaluation_reports_observed_and_limit():
    evaluation = evaluate_season_policy(
        planning_input=create_input(),
        proposal=create_proposal(
            load=360.0,
        ),
        policy=create_policy(
            multiplier=1.10,
        ),
    )

    result = evaluation.evaluations[0]

    assert result.observed_value == 360.0

    assert result.limit_value == 330.0


def test_disabled_rule_is_not_evaluated():
    policy = create_policy()

    disabled = replace(
        policy.rules[0],
        enabled=False,
    )

    policy = replace(
        policy,
        rules=(
            disabled,
        ),
    )

    evaluation = evaluate_season_policy(
        planning_input=create_input(),
        proposal=create_proposal(),
        policy=policy,
    )

    assert evaluation.evaluations == ()

def test_hard_limit_without_evaluator_is_unevaluable() -> None:
    policy = create_policy(
        authority="hard_limit"
    )

    rule = replace(
        policy.rules[0],
        parameters=None,
    )

    policy = replace(
        policy,
        rules=(
            rule,
        ),
    )

    evaluation = evaluate_season_policy(
        planning_input=create_input(),
        proposal=create_proposal(),
        policy=policy,
    )

    result = evaluation.evaluations[0]

    assert result.status == "unevaluable"

    assert len(
        evaluation.unevaluable_hard_limits
    ) == 1

    assert evaluation.acceptable is False

def test_warning_without_evaluator_remains_not_applicable() -> None:
    policy = create_policy(
        authority="warning"
    )

    rule = replace(
        policy.rules[0],
        parameters=None,
    )

    policy = replace(
        policy,
        rules=(
            rule,
        ),
    )

    evaluation = evaluate_season_policy(
        planning_input=create_input(),
        proposal=create_proposal(),
        policy=policy,
    )

    assert (
        evaluation.evaluations[0].status
        == "not_applicable"
    )

    assert evaluation.acceptable is True