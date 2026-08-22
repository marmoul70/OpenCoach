from dataclasses import replace
from datetime import date
from uuid import uuid4

import pytest

from opencoach.models import (
    AthleteProfile,
    Race,
)
from opencoach.planning import (
    AthleteTrainingBaseline,
    KnowledgeRequirementReason,
    PhysiologicalCalibrationMetric,
    PhysiologicalCalibrationSnapshot,
    SeasonAthleteContext,
    SeasonConstraintContext,
    SeasonGoalContext,
    SeasonKnowledgeContext,
    SeasonPlanningInput,
    SeasonStrategistContext,
    SeasonTrainingState,
    TrainingKnowledgeContext,
    TrainingKnowledgeItem,
    TrainingKnowledgeSource,
    build_season_strategist_context,
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


def create_race(
    *,
    race_date=date(
        2027,
        6,
        12,
    ),
    name="Objectif juin",
):
    return Race(
        id=uuid4(),
        date=race_date,
        name=name,
        location="Test",
        race_type="trail",
        priority="primary",
        distance_km=50.0,
        elevation_gain_m=2500.0,
        status="planned",
    )


def create_planning_input():
    race = create_race()

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
            races=(
                race,
            ),
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


def create_knowledge_context():
    source = TrainingKnowledgeSource(
        source_id="source",
        source_type="systematic_review",
        title="Review",
    )

    item = TrainingKnowledgeItem(
        knowledge_id="knowledge-1",
        topic="periodization",
        statement="Connaissance test.",
        rationale="Justification test.",
        evidence_level="moderate",
        applicability=(
            "general_endurance",
        ),
        sources=(
            source,
        ),
        valid_from=date(
            2027,
            1,
            1,
        ),
    )

    return TrainingKnowledgeContext(
        knowledge_base_id="training-knowledge",
        knowledge_version="2027.03",
        topics=(
            "periodization",
        ),
        applicabilities=(
            "general_endurance",
        ),
        items=(
            item,
        ),
        selection_reasons=(
            KnowledgeRequirementReason(
                requirement="periodization",
                reason="Planification de saison.",
            ),
        ),
    )


def test_strategist_context_combines_input_and_knowledge() -> None:
    planning_input = create_planning_input()
    knowledge = create_knowledge_context()

    context = build_season_strategist_context(
        planning_input=planning_input,
        training_knowledge=knowledge,
    )

    assert isinstance(
        context,
        SeasonStrategistContext,
    )

    assert (
        context.planning_input
        is planning_input
    )

    assert (
        context.training_knowledge
        is knowledge
    )


def test_strategist_context_exposes_knowledge_ids() -> None:
    context = build_season_strategist_context(
        planning_input=create_planning_input(),
        training_knowledge=create_knowledge_context(),
    )

    assert context.knowledge_ids == (
        "knowledge-1",
    )


def test_strategist_context_exposes_target_race() -> None:
    context = build_season_strategist_context(
        planning_input=create_planning_input(),
        training_knowledge=create_knowledge_context(),
    )

    assert (
        context.target_race.name
        == "Objectif juin"
    )


def test_strategist_context_exposes_priority_races() -> None:
    planning_input = create_planning_input()

    may_race = create_race(
        race_date=date(
            2027,
            5,
            10,
        ),
        name="Objectif mai",
    )

    planning_input = replace(
        planning_input,
        goals=SeasonGoalContext(
            target_race=(
                planning_input.goals.target_race
            ),
            races=(
                may_race,
                planning_input.goals.target_race,
            ),
        ),
    )

    context = build_season_strategist_context(
        planning_input=planning_input,
        training_knowledge=create_knowledge_context(),
    )

    assert len(
        context.priority_races
    ) == 2


def test_initial_context_is_not_revision() -> None:
    context = build_season_strategist_context(
        planning_input=create_planning_input(),
        training_knowledge=create_knowledge_context(),
    )

    assert context.is_revision is False


def test_knowledge_version_mismatch_is_rejected() -> None:
    knowledge = replace(
        create_knowledge_context(),
        knowledge_version="different-version",
    )

    with pytest.raises(
        ValueError,
        match="version des connaissances",
    ):
        build_season_strategist_context(
            planning_input=create_planning_input(),
            training_knowledge=knowledge,
        )


def test_context_contains_no_python_policy() -> None:
    context = build_season_strategist_context(
        planning_input=create_planning_input(),
        training_knowledge=create_knowledge_context(),
    )

    assert not hasattr(
        context,
        "policy",
    )

    assert not hasattr(
        context,
        "hard_limits",
    )
