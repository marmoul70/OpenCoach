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
    SeasonAthleteContext,
    SeasonConstraintContext,
    SeasonGoalContext,
    SeasonKnowledgeContext,
    SeasonPlanningInput,
    SeasonTrainingState,
    TrainingKnowledgeBase,
    TrainingKnowledgeItem,
    TrainingKnowledgeSource,
    infer_training_knowledge_requirements,
    select_training_knowledge,
    RaceClassificationThresholds,
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


def create_source():
    return TrainingKnowledgeSource(
        source_id="source",
        source_type="systematic_review",
        title="Review",
    )


def create_item(
    *,
    knowledge_id,
    topic,
    applicability,
):
    return TrainingKnowledgeItem(
        knowledge_id=knowledge_id,
        topic=topic,
        statement="Connaissance test.",
        rationale="Justification test.",
        evidence_level="moderate",
        applicability=tuple(
            applicability
        ),
        sources=(
            create_source(),
        ),
        valid_from=date(
            2027,
            1,
            1,
        ),
    )


def create_base():
    return TrainingKnowledgeBase(
        knowledge_base_id="training-knowledge",
        version="2027.03",
        effective_from=date(
            2027,
            1,
            1,
        ),
        items=(
            create_item(
                knowledge_id="trail-specificity",
                topic="specificity",
                applicability=(
                    "trail_running",
                    "long_trail",
                ),
            ),
            create_item(
                knowledge_id="general-load",
                topic="load_progression",
                applicability=(
                    "general_endurance",
                ),
            ),
            create_item(
                knowledge_id="road-10k",
                topic="race_preparation",
                applicability=(
                    "10k",
                    "road_running",
                ),
            ),
        ),
    )


def test_strategy_requires_core_training_topics() -> None:
    requirements = (
        infer_training_knowledge_requirements(
            planning_input=create_input(),
            race_thresholds=create_thresholds(),
        )
    )

    assert {
        "periodization",
        "load_progression",
        "recovery",
        "taper",
        "specificity",
        "race_preparation",
    }.issubset(
        set(requirements.topics)
    )


def test_endurance_is_always_applicable() -> None:
    requirements = (
        infer_training_knowledge_requirements(
            planning_input=create_input(),
            race_thresholds=create_thresholds(),
        )
    )

    assert (
        "general_endurance"
        in requirements.applicabilities
    )


def test_trail_race_requires_trail_knowledge() -> None:
    requirements = (
        infer_training_knowledge_requirements(
            planning_input=create_input(),
            race_thresholds=create_thresholds(),
        )
    )

    assert (
        "trail_running"
        in requirements.applicabilities
    )


def test_missing_physiology_requires_assessment_knowledge() -> None:
    requirements = (
        infer_training_knowledge_requirements(
            planning_input=create_input(),
            race_thresholds=create_thresholds(),
        )
    )

    assert (
        "physiological_assessment"
        in requirements.topics
    )


def test_requirements_are_explainable() -> None:
    requirements = (
        infer_training_knowledge_requirements(
            planning_input=create_input(),
            race_thresholds=create_thresholds(),
        )
    )

    assert requirements.reasons

    assert all(
        reason.requirement
        and reason.reason
        for reason in requirements.reasons
    )


def test_inferred_requirements_can_drive_selection() -> None:
    planning_input = create_input()

    requirements = (
        infer_training_knowledge_requirements(
            planning_input=create_input(),
            race_thresholds=create_thresholds(),
        )
    )

    selection = select_training_knowledge(
        planning_input=planning_input,
        knowledge_base=create_base(),
        topics=requirements.topics,
        applicabilities=(
            requirements.applicabilities
        ),
    )

    assert (
        "trail-specificity"
        in selection.knowledge_ids
    )

    assert (
        "road-10k"
        not in selection.knowledge_ids
    )

def create_thresholds():
    return RaceClassificationThresholds(
        road_short_max_km=12.0,
        road_middle_max_km=25.0,
        road_long_max_km=45.0,
        trail_short_max_km=25.0,
        trail_middle_max_km=50.0,
        trail_long_max_km=80.0,
        rolling_elevation_ratio=20.0,
        mountain_elevation_ratio=50.0,
    )

def test_long_trail_applicability_is_inferred() -> None:
    requirements = (
        infer_training_knowledge_requirements(
            planning_input=create_input(),
            race_thresholds=create_thresholds(),
        )
    )

    assert (
        "long_trail"
        in requirements.applicabilities
    )


def test_race_classification_reason_is_exposed() -> None:
    requirements = (
        infer_training_knowledge_requirements(
            planning_input=create_input(),
            race_thresholds=create_thresholds(),
        )
    )

    assert any(
        "trail/middle"
        in reason.reason
        for reason in requirements.reasons
    )