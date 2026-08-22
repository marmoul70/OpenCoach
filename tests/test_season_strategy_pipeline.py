from dataclasses import replace
from datetime import date, datetime, timezone
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
    SeasonStrategy,
    StrategyRevision,
    StrategyRevisionChange,
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
            target_race=race,
            races=(),
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
        "phase_not_after_target_race"
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
def test_policy_version_mismatch_rejects_strategy() -> None:
    planning_input = create_planning_input()

    changed_policy = replace(
        create_policy(),
        version="2.0",
    )

    result = evaluate_season_strategy_gate(
        planning_input=planning_input,
        proposal=create_valid_proposal(),
        policy=changed_policy,
    )

    assert result.status == "reject"

    assert any(
        "policy_version_mismatch"
        in reason
        for reason in result.reasons
    )

def test_future_policy_rejects_strategy() -> None:
    planning_input = create_planning_input()

    changed_policy = replace(
        create_policy(),
        effective_from=date(
            2027,
            4,
            1,
        ),
    )

    result = evaluate_season_strategy_gate(
        planning_input=planning_input,
        proposal=create_valid_proposal(),
        policy=changed_policy,
    )

    assert result.status == "reject"

    assert any(
        "policy_not_effective_yet"
        in reason
        for reason in result.reasons
    )

def create_revision_input():
    planning_input = create_planning_input()

    may_race = Race(
        id=uuid4(),
        date=date(
            2027,
            5,
            10,
        ),
        name="Objectif mai",
        location="Test",
        race_type="trail",
        priority="primary",
        distance_km=30.0,
        elevation_gain_m=1500.0,
        status="planned",
    )

    june_race = planning_input.goals.target_race

    return replace(
        planning_input,
        goals=SeasonGoalContext(
            target_race=june_race,
            races=(
                may_race,
                june_race,
            ),
        ),
        previous_strategy=(
            create_previous_strategy()
        ),
    )

def create_previous_strategy():
    return SeasonStrategy(
        id=uuid4(),
        athlete_profile_id=uuid4(),
        planning_date=date(
            2027,
            1,
            1,
        ),
        target_race_id=uuid4(),
        target_race_date=RACE_DATE,
        phases=(
            MacrocyclePhase(
                phase_type="base",
                start_date=date(
                    2027,
                    1,
                    1,
                ),
                end_date=date(
                    2027,
                    2,
                    28,
                ),
                objective=(
                    "Construire la base aérobie."
                ),
                primary_stimuli=(
                    "aerobic_endurance",
                ),
            ),
        ),
        weeks=(),
        revision=StrategyRevision(
            reason="initial_plan",
            created_at=datetime(
                2027,
                1,
                1,
                tzinfo=timezone.utc,
            ),
            description=(
                "Stratégie initiale vers juin."
            ),
        ),
        knowledge_version="2027.03",
        policy_version="1.0",
        created_at=datetime(
            2027,
            1,
            1,
            tzinfo=timezone.utc,
        ),
    )

def test_new_priority_race_can_trigger_explicit_strategy_revision() -> None:
    planning_input = create_revision_input()

    proposal = replace(
        create_valid_proposal(),
        revision_changes=(
            StrategyRevisionChange(
                action="modify",
                target="macrocycle:may-june",
                description=(
                    "Intégrer un premier pic de forme "
                    "pour la course prioritaire de mai, "
                    "puis prévoir récupération et "
                    "reconstruction vers juin."
                ),
                reason=(
                    "Une nouvelle course prioritaire "
                    "a été ajoutée le 10 mai."
                ),
            ),
        ),
    )

    result = evaluate_season_strategy_gate(
        planning_input=planning_input,
        proposal=proposal,
        policy=create_policy(),
    )

    assert result.status == "accept"

    assert result.accepted is True

    assert (
        planning_input.is_revision
        is True
    )

    assert len(
        planning_input.goals.priority_races
    ) == 2

    assert {
        race.date
        for race
        in planning_input.goals.priority_races
    } == {
        date(
            2027,
            5,
            10,
        ),
        date(
            2027,
            6,
            12,
        ),
    }

    assert proposal.is_revision is True

def test_revision_input_without_revision_changes_requires_revision() -> None:
    planning_input = create_revision_input()

    proposal = create_valid_proposal()

    result = evaluate_season_strategy_gate(
        planning_input=planning_input,
        proposal=proposal,
        policy=create_policy(),
    )

    assert result.status == "revise"

    assert any(
        "revision_changes_required"
        in reason
        for reason in result.reasons
    )