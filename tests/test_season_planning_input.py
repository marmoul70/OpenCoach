from datetime import (
    date,
    datetime,
    timezone,
)
from uuid import uuid4

import pytest

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
)


PLANNING_DATE = date(
    2027,
    3,
    1,
)


def create_race(
    *,
    race_date=date(
        2027,
        6,
        12,
    ),
):
    return Race(
        id=uuid4(),
        date=race_date,
        name="Course objectif",
        location="Test",
        race_type="trail",
        priority="primary",
        distance_km=50.0,
        elevation_gain_m=2500.0,
        status="planned",
    )


def create_baseline():
    return AthleteTrainingBaseline(
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
    )


def create_missing_metric(
    metric,
):
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


def create_physiology():
    return PhysiologicalCalibrationSnapshot(
        vma=create_missing_metric(
            "vma"
        ),
        max_heart_rate=create_missing_metric(
            "max_heart_rate"
        ),
        resting_heart_rate=create_missing_metric(
            "resting_heart_rate"
        ),
        threshold_heart_rate_1=create_missing_metric(
            "threshold_heart_rate_1"
        ),
        threshold_heart_rate_2=create_missing_metric(
            "threshold_heart_rate_2"
        ),
    )


def create_input(
    *,
    race=None,
):
    if race is None:
        race = create_race()

    return SeasonPlanningInput(
        athlete_profile_id=uuid4(),
        planning_date=PLANNING_DATE,
        athlete=SeasonAthleteContext(
            profile=AthleteProfile(),
            baseline=create_baseline(),
            physiology=create_physiology(),
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


def test_input_is_single_structured_contract() -> None:
    planning_input = create_input()

    assert (
        planning_input.athlete.baseline.weekly_sessions
        == 4.0
    )

    assert (
        planning_input.goals.primary_race.priority
        == "primary"
    )

    assert (
        planning_input.knowledge.knowledge_version
        == "2027.03"
    )


def test_input_calculates_days_to_goal() -> None:
    planning_input = create_input()

    assert (
        planning_input.days_to_primary_race
        == 103
    )


def test_input_calculates_weeks_to_goal() -> None:
    planning_input = create_input()

    assert (
        planning_input.weeks_to_primary_race
        == 15
    )


def test_initial_input_is_not_revision() -> None:
    planning_input = create_input()

    assert planning_input.is_revision is False


def test_future_contract_can_keep_optional_state_missing() -> None:
    planning_input = create_input()

    assert (
        planning_input.training_state.readiness
        is None
    )

    assert (
        planning_input.training_state.recent_load
        is None
    )


def test_past_primary_race_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="course principale",
    ):
        create_input(
            race=create_race(
                race_date=date(
                    2027,
                    2,
                    20,
                )
            )
        )


def test_constraint_horizon_cannot_end_before_planning_date() -> None:
    with pytest.raises(
        ValueError,
        match="contraintes",
    ):
        SeasonPlanningInput(
            athlete_profile_id=uuid4(),
            planning_date=PLANNING_DATE,
            athlete=SeasonAthleteContext(
                profile=AthleteProfile(),
                baseline=create_baseline(),
                physiology=create_physiology(),
            ),
            goals=SeasonGoalContext(
                primary_race=create_race(),
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
                    2,
                    28,
                ),
            ),
            knowledge=SeasonKnowledgeContext(
                knowledge_version="2027.03",
                policy_version="season-planning-v1",
            ),
        )
