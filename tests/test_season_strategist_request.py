import json
from datetime import (
    date,
    datetime,
    timezone,
)
from uuid import uuid4

import pytest

from opencoach.planning import (
    SeasonStrategistRequest,
    build_season_strategist_request,
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
    build_season_strategist_request,
)

from opencoach.planning.season_strategist_request import (
    _serialize_value,
)
from opencoach.models import (
    AthleteProfile,
    Race,
)

def test_serializer_converts_uuid() -> None:
    value = uuid4()

    serialized = _serialize_value(
        value
    )

    assert serialized == str(
        value
    )


def test_serializer_converts_date() -> None:
    serialized = _serialize_value(
        date(
            2027,
            6,
            12,
        )
    )

    assert serialized == "2027-06-12"


def test_serializer_converts_datetime() -> None:
    serialized = _serialize_value(
        datetime(
            2027,
            6,
            12,
            8,
            30,
            tzinfo=timezone.utc,
        )
    )

    assert serialized == (
        "2027-06-12T08:30:00+00:00"
    )


def test_serializer_converts_nested_tuple() -> None:
    serialized = _serialize_value(
        (
            "one",
            date(
                2027,
                6,
                12,
            ),
        )
    )

    assert serialized == [
        "one",
        "2027-06-12",
    ]


def test_serializer_rejects_unknown_type() -> None:
    class Unsupported:
        pass

    with pytest.raises(
        TypeError,
        match="non sérialisable",
    ):
        _serialize_value(
            Unsupported()
        )


def test_request_is_json_serializable() -> None:
    request = SeasonStrategistRequest(
        schema_version="1.0",
        planning={
            "planning_date": "2027-03-01",
            "athlete_profile_id": str(
                uuid4()
            ),
        },
        knowledge={
            "knowledge_version": "2027.03",
            "items": [],
        },
        instructions={
            "output_contract": (
                "SeasonStrategyProposal"
            ),
        },
    )

    payload = {
        "schema_version": (
            request.schema_version
        ),
        "planning": request.planning,
        "knowledge": request.knowledge,
        "instructions": (
            request.instructions
        ),
    }

    encoded = json.dumps(
        payload
    )

    assert isinstance(
        encoded,
        str,
    )


def test_request_contains_no_python_policy_contract() -> None:
    request = SeasonStrategistRequest(
        schema_version="1.0",
        planning={},
        knowledge={},
        instructions={},
    )

    assert not hasattr(
        request,
        "policy",
    )

    assert not hasattr(
        request,
        "hard_limits",
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


def create_real_context():
    june_race = Race(
        id=uuid4(),
        date=date(
            2027,
            6,
            12,
        ),
        name="Objectif juin",
        location="Test",
        race_type="trail",
        priority="primary",
        distance_km=50.0,
        elevation_gain_m=2500.0,
        status="planned",
    )

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

    planning_input = SeasonPlanningInput(
        athlete_profile_id=uuid4(),
        planning_date=date(
            2027,
            3,
            1,
        ),
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
            target_race=june_race,
            races=(
                may_race,
                june_race,
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

    source = TrainingKnowledgeSource(
        source_id="review-2027",
        source_type="systematic_review",
        title="Endurance review",
        publication_year=2027,
    )

    item = TrainingKnowledgeItem(
        knowledge_id="trail-periodization",
        topic="periodization",
        statement=(
            "La préparation doit évoluer progressivement "
            "vers les exigences spécifiques de la course."
        ),
        rationale=(
            "La spécificité augmente à l'approche "
            "de l'objectif."
        ),
        evidence_level="moderate",
        applicability=(
            "general_endurance",
            "trail_running",
            "long_trail",
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

    knowledge = TrainingKnowledgeContext(
        knowledge_base_id="training-knowledge",
        knowledge_version="2027.03",
        topics=(
            "periodization",
        ),
        applicabilities=(
            "general_endurance",
            "trail_running",
            "long_trail",
        ),
        items=(
            item,
        ),
        selection_reasons=(
            KnowledgeRequirementReason(
                requirement="long_trail",
                reason=(
                    "La course cible est classée long trail."
                ),
            ),
        ),
    )

    return SeasonStrategistContext(
        planning_input=planning_input,
        training_knowledge=knowledge,
    )

def test_real_context_builds_provider_agnostic_request() -> None:
    request = build_season_strategist_request(
        context=create_real_context(),
    )

    assert request.schema_version == "1.0"

    assert (
        request.planning["planning_date"]
        == "2027-03-01"
    )

    assert (
        request.knowledge["knowledge_version"]
        == "2027.03"
    )


def test_real_request_contains_both_priority_races() -> None:
    request = build_season_strategist_request(
        context=create_real_context(),
    )

    races = request.planning["goals"]["priority_races"]

    assert len(races) == 2

    assert {
        race["name"]
        for race in races
    } == {
        "Objectif mai",
        "Objectif juin",
    }


def test_real_request_contains_selected_knowledge() -> None:
    request = build_season_strategist_request(
        context=create_real_context(),
    )

    items = request.knowledge["items"]

    assert len(items) == 1

    assert (
        items[0]["knowledge_id"]
        == "trail-periodization"
    )


def test_real_request_can_be_encoded_as_json() -> None:
    request = build_season_strategist_request(
        context=create_real_context(),
    )

    payload = {
        "schema_version": request.schema_version,
        "planning": request.planning,
        "knowledge": request.knowledge,
        "instructions": request.instructions,
    }

    encoded = json.dumps(
        payload,
        ensure_ascii=False,
    )

    decoded = json.loads(
        encoded
    )

    assert (
        decoded["planning"]["goals"]["target_race"]["name"]
        == "Objectif juin"
    )

    assert (
        decoded["knowledge"]["items"][0]["knowledge_id"]
        == "trail-periodization"
    )

def test_serializer_keeps_date_and_datetime_distinct() -> None:
    serialized_date = _serialize_value(
        date(
            2027,
            6,
            12,
        )
    )

    serialized_datetime = _serialize_value(
        datetime(
            2027,
            6,
            12,
            8,
            30,
            tzinfo=timezone.utc,
        )
    )

    assert serialized_date == "2027-06-12"

    assert serialized_datetime == (
        "2027-06-12T08:30:00+00:00"
    )

    assert (
        serialized_date
        != serialized_datetime
    )