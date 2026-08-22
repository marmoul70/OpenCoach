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
    select_training_knowledge,
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
    evidence_level="moderate",
    valid_from=date(
        2027,
        1,
        1,
    ),
    valid_until=None,
):
    return TrainingKnowledgeItem(
        knowledge_id=knowledge_id,
        topic=topic,
        statement="Connaissance test.",
        rationale="Justification test.",
        evidence_level=evidence_level,
        applicability=tuple(
            applicability
        ),
        sources=(
            create_source(),
        ),
        valid_from=valid_from,
        valid_until=valid_until,
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
                evidence_level="high",
            ),
            create_item(
                knowledge_id="general-load",
                topic="load_progression",
                applicability=(
                    "general_endurance",
                ),
                evidence_level="moderate",
            ),
            create_item(
                knowledge_id="road-10k",
                topic="race_preparation",
                applicability=(
                    "10k",
                    "road_running",
                ),
                evidence_level="high",
            ),
            create_item(
                knowledge_id="expired",
                topic="recovery",
                applicability=(
                    "general_endurance",
                ),
                valid_from=date(
                    2025,
                    1,
                    1,
                ),
                valid_until=date(
                    2026,
                    12,
                    31,
                ),
            ),
        ),
    )


def test_selection_filters_by_topic() -> None:
    selection = select_training_knowledge(
        planning_input=create_input(),
        knowledge_base=create_base(),
        topics=(
            "specificity",
        ),
    )

    assert selection.knowledge_ids == (
        "trail-specificity",
    )


def test_selection_filters_by_applicability() -> None:
    selection = select_training_knowledge(
        planning_input=create_input(),
        knowledge_base=create_base(),
        applicabilities=(
            "long_trail",
        ),
    )

    assert selection.knowledge_ids == (
        "trail-specificity",
    )


def test_selection_excludes_expired_items() -> None:
    selection = select_training_knowledge(
        planning_input=create_input(),
        knowledge_base=create_base(),
    )

    assert "expired" not in (
        selection.knowledge_ids
    )


def test_selection_can_require_minimum_evidence() -> None:
    selection = select_training_knowledge(
        planning_input=create_input(),
        knowledge_base=create_base(),
        minimum_evidence_level="high",
    )

    assert set(
        selection.knowledge_ids
    ) == {
        "trail-specificity",
        "road-10k",
    }


def test_filters_are_combined() -> None:
    selection = select_training_knowledge(
        planning_input=create_input(),
        knowledge_base=create_base(),
        topics=(
            "specificity",
            "load_progression",
        ),
        applicabilities=(
            "trail_running",
        ),
    )

    assert selection.knowledge_ids == (
        "trail-specificity",
    )


def test_empty_selection_is_explicit() -> None:
    selection = select_training_knowledge(
        planning_input=create_input(),
        knowledge_base=create_base(),
        topics=(
            "taper",
        ),
        applicabilities=(
            "marathon",
        ),
    )

    assert selection.empty is True
    assert selection.items == ()


def test_selection_preserves_knowledge_version() -> None:
    selection = select_training_knowledge(
        planning_input=create_input(),
        knowledge_base=create_base(),
    )

    assert (
        selection.knowledge_base_id
        == "training-knowledge"
    )

    assert (
        selection.knowledge_version
        == "2027.03"
    )