from dataclasses import replace
from datetime import (
    date,
    datetime,
    timezone,
)
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
    SeasonAthleteContext,
    SeasonConstraintContext,
    SeasonGoalContext,
    SeasonKnowledgeContext,
    SeasonPlanningInput,
    SeasonStrategyProposal,
    SeasonTrainingState,
    StrategyFactReference,
    StrategyRevisionChange,
    TrainingStimulus,
    WeekTrajectory,
    validate_season_strategy_proposal,
)


PLANNING_DATE = date(2027, 3, 1)
RACE_DATE = date(2027, 6, 12)


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
        date=RACE_DATE,
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
            primary_race=race,
        ),
        training_state=SeasonTrainingState(
            recent_load=None,
            recent_stats=None,
            readiness=None,
        ),
        constraints=SeasonConstraintContext(
            constraints=(),
            known_until=date(2027, 3, 14),
        ),
        knowledge=SeasonKnowledgeContext(
            knowledge_version="2027.03",
            policy_version="season-planning-v1",
        ),
    )


def create_phase(
    *,
    start=PLANNING_DATE,
    end=date(2027, 3, 28),
):
    return MacrocyclePhase(
        phase_type="build",
        start_date=start,
        end_date=end,
        objective="Développer la capacité.",
        primary_stimuli=(
            "aerobic_endurance",
        ),
    )


def create_week(
    *,
    number=1,
    start=PLANNING_DATE,
    end=date(2027, 3, 7),
):
    return WeekTrajectory(
        week_number=number,
        start_date=start,
        end_date=end,
        phase="build",
        target_load=300.0,
        load_min=280.0,
        load_max=320.0,
        target_duration_minutes=300,
        target_distance_km=45.0,
        target_elevation_gain_m=800.0,
        primary_stimuli=(
            TrainingStimulus(
                stimulus_type="aerobic_endurance",
                priority="high",
            ),
        ),
    )


def create_proposal():
    return SeasonStrategyProposal(
        summary="Stratégie de test.",
        facts_used=(
            StrategyFactReference(
                source_path=(
                    "athlete.baseline.weekly_distance_km"
                ),
                purpose="Dimensionner la charge.",
            ),
        ),
        assumptions=(),
        decisions=(),
        uncertainties=(),
        phases=(
            create_phase(),
        ),
        weeks=(
            create_week(),
        ),
    )


def rule_ids(validation):
    return {
        violation.rule_id
        for violation in validation.violations
    }


def test_valid_proposal_passes_validation():
    validation = validate_season_strategy_proposal(
        planning_input=create_input(),
        proposal=create_proposal(),
    )

    assert validation.valid is True
    assert validation.errors == ()


def test_unknown_fact_reference_is_rejected():
    proposal = replace(
        create_proposal(),
        facts_used=(
            StrategyFactReference(
                source_path="athlete.baseline.does_not_exist",
                purpose="Test.",
            ),
        ),
    )

    validation = validate_season_strategy_proposal(
        planning_input=create_input(),
        proposal=proposal,
    )

    assert validation.valid is False

    assert (
        "fact_reference_exists"
        in rule_ids(validation)
    )


def test_phase_after_primary_race_is_rejected():
    proposal = replace(
        create_proposal(),
        phases=(
            create_phase(
                start=date(2027, 6, 10),
                end=date(2027, 6, 20),
            ),
        ),
    )

    validation = validate_season_strategy_proposal(
        planning_input=create_input(),
        proposal=proposal,
    )

    assert (
        "phase_not_after_primary_race"
        in rule_ids(validation)
    )


def test_overlapping_phases_are_rejected():
    proposal = replace(
        create_proposal(),
        phases=(
            create_phase(
                start=date(2027, 3, 1),
                end=date(2027, 3, 20),
            ),
            create_phase(
                start=date(2027, 3, 15),
                end=date(2027, 4, 1),
            ),
        ),
    )

    validation = validate_season_strategy_proposal(
        planning_input=create_input(),
        proposal=proposal,
    )

    assert (
        "phase_no_overlap"
        in rule_ids(validation)
    )


def test_duplicate_week_numbers_are_rejected():
    proposal = replace(
        create_proposal(),
        weeks=(
            create_week(
                number=1,
                start=date(2027, 3, 1),
                end=date(2027, 3, 7),
            ),
            create_week(
                number=1,
                start=date(2027, 3, 8),
                end=date(2027, 3, 14),
            ),
        ),
    )

    validation = validate_season_strategy_proposal(
        planning_input=create_input(),
        proposal=proposal,
    )

    assert (
        "week_number_unique"
        in rule_ids(validation)
    )


def test_overlapping_weeks_are_rejected():
    proposal = replace(
        create_proposal(),
        weeks=(
            create_week(
                number=1,
                start=date(2027, 3, 1),
                end=date(2027, 3, 8),
            ),
            create_week(
                number=2,
                start=date(2027, 3, 8),
                end=date(2027, 3, 14),
            ),
        ),
    )

    validation = validate_season_strategy_proposal(
        planning_input=create_input(),
        proposal=proposal,
    )

    assert (
        "week_no_overlap"
        in rule_ids(validation)
    )


def test_revision_without_previous_strategy_is_rejected():
    proposal = replace(
        create_proposal(),
        revision_changes=(
            StrategyRevisionChange(
                action="modify",
                target="phase:build",
                description="Modifier le bloc.",
                reason="Nouvel objectif.",
            ),
        ),
    )

    validation = validate_season_strategy_proposal(
        planning_input=create_input(),
        proposal=proposal,
    )

    assert (
        "revision_without_previous_strategy"
        in rule_ids(validation)
    )


def test_private_or_dynamic_fact_path_is_rejected():
    proposal = replace(
        create_proposal(),
        facts_used=(
            StrategyFactReference(
                source_path="athlete.__class__",
                purpose="Test.",
            ),
        ),
    )

    validation = validate_season_strategy_proposal(
        planning_input=create_input(),
        proposal=proposal,
    )

    assert (
        "fact_reference_exists"
        in rule_ids(validation)
    )
