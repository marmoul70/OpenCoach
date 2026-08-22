from dataclasses import replace
from datetime import date
from uuid import uuid4

from opencoach.models import (
    AthleteProfile,
    Race,
)
from opencoach.planning import (
    AthleteTrainingBaseline,
    MacrocyclePhase,
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
    StrategyDecision,
    StrategyFactReference,
    TrainingStimulus,
    WeekTrajectory,
    evaluate_season_strategy_gate,
)


PLANNING_DATE = date(
    2027,
    3,
    1,
)

RACE_DATE = date(
    2027,
    6,
    12,
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


def create_planning_input():
    race = Race(
        id=uuid4(),
        date=RACE_DATE,
        name="Trail objectif",
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
                reasons=(
                    "Historique suffisant.",
                ),
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
            primary_race=race,
            training_races=(),
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
            policy_version="season-planning-v1",
        ),
    )


def create_week(
    *,
    number,
    start,
    end,
    target_load,
):
    return WeekTrajectory(
        week_number=number,
        start_date=start,
        end_date=end,
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
            TrainingStimulus(
                stimulus_type="threshold",
                priority="medium",
            ),
        ),
    )


def create_valid_proposal(
    *,
    load=330.0,
):
    fact_path = (
        "athlete.baseline.weekly_training_load"
    )

    return SeasonStrategyProposal(
        summary=(
            "Progression contrôlée vers la course principale."
        ),
        facts_used=(
            StrategyFactReference(
                source_path=fact_path,
                purpose=(
                    "Dimensionner la charge stratégique."
                ),
            ),
        ),
        assumptions=(),
        decisions=(
            StrategyDecision(
                decision_type="load_progression",
                description=(
                    "Augmenter progressivement la charge."
                ),
                rationale=(
                    "La baseline démontrée permet "
                    "une progression contrôlée."
                ),
                based_on_facts=(
                    fact_path,
                ),
            ),
        ),
        uncertainties=(),
        phases=(
            MacrocyclePhase(
                phase_type="build",
                start_date=date(
                    2027,
                    3,
                    1,
                ),
                end_date=date(
                    2027,
                    3,
                    28,
                ),
                objective=(
                    "Développer la capacité d'entraînement."
                ),
                primary_stimuli=(
                    "aerobic_endurance",
                    "threshold",
                ),
            ),
        ),
        weeks=(
            create_week(
                number=1,
                start=date(
                    2027,
                    3,
                    1,
                ),
                end=date(
                    2027,
                    3,
                    7,
                ),
                target_load=load,
            ),
        ),
    )


def create_policy(
    *,
    authority="hard_limit",
    multiplier=1.15,
):
    source = PolicySource(
        source_id="open-coach-test",
        source_type="open_coach",
        title="OpenCoach integration policy",
    )

    return SeasonPlanningPolicy(
        policy_id="season-planning",
        version="1.0",
        effective_from=PLANNING_DATE,
        rules=(
            SeasonPolicyRule(
                rule_id="baseline-load-cap",
                category="load_progression",
                authority=authority,
                description=(
                    "Limiter le pic de charge "
                    "par rapport à la baseline."
                ),
                rationale=(
                    "Protection contre une proposition "
                    "trop agressive."
                ),
                sources=(
                    source,
                ),
                parameters=RelativeLoadLimitParameters(
                    reference="baseline",
                    max_multiplier=multiplier,
                ),
            ),
        ),
    )


def test_valid_ai_proposal_is_accepted_by_python() -> None:
    result = evaluate_season_strategy_gate(
        planning_input=create_planning_input(),
        proposal=create_valid_proposal(
            load=330.0,
        ),
        policy=create_policy(
            multiplier=1.15,
        ),
    )

    assert result.status == "accept"

    assert result.accepted is True
    assert result.reasons == ()


def test_aggressive_ai_load_is_sent_back_for_revision() -> None:
    result = evaluate_season_strategy_gate(
        planning_input=create_planning_input(),
        proposal=create_valid_proposal(
            load=400.0,
        ),
        policy=create_policy(
            authority="hard_limit",
            multiplier=1.15,
        ),
    )

    assert result.status == "revise"

    assert result.accepted is False
    assert result.requires_revision is True

    assert any(
        "baseline-load-cap"
        in reason
        for reason in result.reasons
    )


def test_warning_policy_keeps_proposal_acceptable() -> None:
    result = evaluate_season_strategy_gate(
        planning_input=create_planning_input(),
        proposal=create_valid_proposal(
            load=400.0,
        ),
        policy=create_policy(
            authority="warning",
            multiplier=1.15,
        ),
    )

    assert (
        result.status
        == "accept_with_warnings"
    )

    assert result.accepted is True


def test_structurally_invalid_ai_proposal_requires_revision() -> None:
    proposal = replace(
        create_valid_proposal(),
        phases=(
            MacrocyclePhase(
                phase_type="build",
                start_date=date(
                    2027,
                    6,
                    10,
                ),
                end_date=date(
                    2027,
                    6,
                    20,
                ),
                objective="Phase invalide.",
                primary_stimuli=(
                    "aerobic_endurance",
                ),
            ),
        ),
    )

    result = evaluate_season_strategy_gate(
        planning_input=create_planning_input(),
        proposal=proposal,
        policy=create_policy(),
    )

    assert result.status == "revise"

    assert any(
        "phase_not_after_primary_race"
        in reason
        for reason in result.reasons
    )


def test_ai_cannot_reference_fact_that_python_does_not_have() -> None:
    proposal = replace(
        create_valid_proposal(),
        facts_used=(
            StrategyFactReference(
                source_path=(
                    "athlete.baseline.magic_metric"
                ),
                purpose="Donnée inventée.",
            ),
        ),
        decisions=(),
    )

    result = evaluate_season_strategy_gate(
        planning_input=create_planning_input(),
        proposal=proposal,
        policy=create_policy(),
    )

    assert result.status == "revise"

    assert any(
        "fact_reference_exists"
        in reason
        for reason in result.reasons
    )
