from datetime import date
from uuid import uuid4

from opencoach.models import (
    AthleteProfile,
    Race,
)
from opencoach.planning import (
    AthleteTrainingBaseline,
    FakeSeasonStrategist,
    KnowledgeRequirementReason,
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
    SeasonStrategistContext,
    SeasonStrategistResponse,
    SeasonStrategistService,
    SeasonTrainingState,
    TrainingKnowledgeContext,
    TrainingKnowledgeItem,
    TrainingKnowledgeSource,
    SeasonStrategistPort,
)


PLANNING_DATE = date(
    2027,
    3,
    1,
)

TARGET_RACE_DATE = date(
    2027,
    6,
    12,
)

class SequencedSeasonStrategist(
    SeasonStrategistPort
):
    """Fake retournant une réponse différente à chaque appel."""

    def __init__(
        self,
        *responses,
    ):
        self.responses = responses
        self.calls = 0
        self.requests = []

    def generate(
        self,
        *,
        request,
    ):
        self.requests.append(
            request
        )

        response = self.responses[
            self.calls
        ]

        self.calls += 1

        return response

def missing_metric(
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


def create_race():
    return Race(
        id=uuid4(),
        date=TARGET_RACE_DATE,
        name="Trail objectif",
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
                vma=missing_metric(
                    "vma"
                ),
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
        source_id="review",
        source_type="systematic_review",
        title="Review",
    )

    item = TrainingKnowledgeItem(
        knowledge_id="load-progression",
        topic="load_progression",
        statement=(
            "La progression de charge doit être individualisée."
        ),
        rationale=(
            "La tolérance varie selon l'athlète."
        ),
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
            "load_progression",
        ),
        applicabilities=(
            "general_endurance",
        ),
        items=(
            item,
        ),
        selection_reasons=(
            KnowledgeRequirementReason(
                requirement="load_progression",
                reason="Planification de saison.",
            ),
        ),
    )


def create_context():
    return SeasonStrategistContext(
        planning_input=(
            create_planning_input()
        ),
        training_knowledge=(
            create_knowledge_context()
        ),
    )


def create_policy():
    return SeasonPlanningPolicy(
        policy_id="season-planning",
        version="1.0",
        effective_from=PLANNING_DATE,
        rules=(
            SeasonPolicyRule(
                rule_id="baseline-load-cap",
                category="load",
                authority="hard_limit",
                description=(
                    "Limiter la progression par rapport "
                    "à la charge de référence."
                ),
                rationale=(
                    "Éviter une augmentation excessive "
                    "de la charge hebdomadaire."
                ),
                parameters=RelativeLoadLimitParameters(
                    reference="baseline",
                    max_multiplier=1.15,
                ),
                sources=(
                    PolicySource(
                        source_id="test-policy-source",
                        source_type="open_coach",
                        title="Politique de test",
                        reference="test",
                    ),
                ),
            ),
        ),
    )


def create_valid_response(
    *,
    target_load=330.0,
):
    return SeasonStrategistResponse(
        model="fake-local-model",
        content={
            "summary": (
                "Progression vers la course cible."
            ),
            "facts_used": [
                {
                    "source_path": (
                        "athlete.baseline.weekly_training_load"
                    ),
                    "purpose": (
                        "Dimensionner la progression."
                    ),
                },
            ],
            "assumptions": [],
            "decisions": [
                {
                    "decision_type": (
                        "load_progression"
                    ),
                    "description": (
                        "Progression contrôlée."
                    ),
                    "rationale": (
                        "La baseline sert de référence."
                    ),
                    "based_on_facts": [
                        (
                            "athlete.baseline."
                            "weekly_training_load"
                        ),
                    ],
                    "based_on_assumptions": [],
                },
            ],
            "uncertainties": [],
            "phases": [
                {
                    "phase_type": "build",
                    "start_date": (
                        "2027-03-01"
                    ),
                    "end_date": (
                        "2027-03-28"
                    ),
                    "objective": (
                        "Développer progressivement "
                        "la capacité d'entraînement."
                    ),
                    "primary_stimuli": [
                        "aerobic_endurance",
                    ],
                },
            ],
            "weeks": [
                {
                    "week_number": 1,
                    "start_date": (
                        "2027-03-01"
                    ),
                    "end_date": (
                        "2027-03-07"
                    ),
                    "phase": "build",
                    "target_load": target_load,
                    "load_min": (
                        target_load - 10.0
                    ),
                    "load_max": (
                        target_load + 10.0
                    ),
                    "target_duration_minutes": 320,
                    "target_distance_km": 48.0,
                    "target_elevation_gain_m": 1100.0,
                    "primary_stimuli": [
                        {
                            "stimulus_type": (
                                "aerobic_endurance"
                            ),
                            "priority": "high",
                            "target_exposure_minutes": None,
                            "notes": None,
                        },
                    ],
                    "recovery_week": False,
                    "status": "planned",
                    "notes": None,
                },
            ],
            "revision_changes": [],
        },
    )


def test_service_calls_strategist_once() -> None:
    strategist = FakeSeasonStrategist(
        response=create_valid_response(),
    )

    service = SeasonStrategistService(
        strategist=strategist,
    )

    service.execute(
        context=create_context(),
        policy=create_policy(),
    )

    assert strategist.calls == 1


def test_service_builds_request_for_strategist() -> None:
    strategist = FakeSeasonStrategist(
        response=create_valid_response(),
    )

    service = SeasonStrategistService(
        strategist=strategist,
    )

    execution = service.execute(
        context=create_context(),
        policy=create_policy(),
    )

    assert (
        strategist.last_request
        is execution.request
    )

    assert (
        execution.request.schema_version
        == "1.0"
    )


def test_service_parses_ai_response() -> None:
    strategist = FakeSeasonStrategist(
        response=create_valid_response(),
    )

    execution = SeasonStrategistService(
        strategist=strategist,
    ).execute(
        context=create_context(),
        policy=create_policy(),
    )

    assert (
        execution.proposal.summary
        == "Progression vers la course cible."
    )

    assert (
        execution.response.model
        == "fake-local-model"
    )


def test_valid_ai_proposal_is_accepted() -> None:
    strategist = FakeSeasonStrategist(
        response=create_valid_response(
            target_load=330.0,
        ),
    )

    execution = SeasonStrategistService(
        strategist=strategist,
    ).execute(
        context=create_context(),
        policy=create_policy(),
    )

    assert execution.gate.status == "accept"

    assert execution.accepted is True

    assert execution.requires_revision is False

    assert execution.rejected is False


def test_excessive_ai_load_is_not_accepted() -> None:
    strategist = FakeSeasonStrategist(
        response=create_valid_response(
            target_load=400.0,
        ),
    )

    execution = SeasonStrategistService(
        strategist=strategist,
    ).execute(
        context=create_context(),
        policy=create_policy(),
    )

    assert execution.gate.status == "revise"

    assert execution.accepted is False

    assert execution.requires_revision is True


def test_execution_preserves_full_trace() -> None:
    response = create_valid_response()

    strategist = FakeSeasonStrategist(
        response=response,
    )

    execution = SeasonStrategistService(
        strategist=strategist,
    ).execute(
        context=create_context(),
        policy=create_policy(),
    )

    assert execution.response is response

    assert execution.request is not None
    assert execution.proposal is not None
    assert execution.gate is not None

def test_service_revises_then_accepts() -> None:
    strategist = SequencedSeasonStrategist(
        create_valid_response(
            target_load=400.0,
        ),
        create_valid_response(
            target_load=330.0,
        ),
    )

    execution = SeasonStrategistService(
        strategist=strategist,
        max_attempts=3,
    ).execute(
        context=create_context(),
        policy=create_policy(),
    )

    assert strategist.calls == 2

    assert execution.attempt_count == 2

    assert (
        execution.attempts[0].gate.status
        == "revise"
    )

    assert (
        execution.attempts[1].gate.status
        == "accept"
    )

    assert execution.accepted is True


def test_revision_request_contains_gate_feedback() -> None:
    strategist = SequencedSeasonStrategist(
        create_valid_response(
            target_load=400.0,
        ),
        create_valid_response(
            target_load=330.0,
        ),
    )

    execution = SeasonStrategistService(
        strategist=strategist,
        max_attempts=3,
    ).execute(
        context=create_context(),
        policy=create_policy(),
    )

    assert len(
        strategist.requests
    ) == 2

    revision_request = (
        strategist.requests[1]
    )

    feedback = (
        revision_request.instructions[
            "revision_feedback"
        ]
    )

    assert feedback[
        "attempt_number"
    ] == 2

    assert feedback[
        "reasons"
    ]

    previous_proposal = (
        feedback["previous_proposal"]
    )

    assert (
        previous_proposal["summary"]
        == "Progression vers la course cible."
    )

    assert (
        previous_proposal["weeks"][0]["target_load"]
        == 400.0
    )


def test_revision_does_not_mutate_initial_request() -> None:
    strategist = SequencedSeasonStrategist(
        create_valid_response(
            target_load=400.0,
        ),
        create_valid_response(
            target_load=330.0,
        ),
    )

    SeasonStrategistService(
        strategist=strategist,
    ).execute(
        context=create_context(),
        policy=create_policy(),
    )

    initial_request = (
        strategist.requests[0]
    )

    revised_request = (
        strategist.requests[1]
    )

    assert (
        "revision_feedback"
        not in initial_request.instructions
    )

    assert (
        "revision_feedback"
        in revised_request.instructions
    )

    assert (
        initial_request
        is not revised_request
    )


def test_service_stops_after_max_attempts() -> None:
    strategist = SequencedSeasonStrategist(
        create_valid_response(
            target_load=400.0,
        ),
        create_valid_response(
            target_load=400.0,
        ),
        create_valid_response(
            target_load=330.0,
        ),
    )

    execution = SeasonStrategistService(
        strategist=strategist,
        max_attempts=2,
    ).execute(
        context=create_context(),
        policy=create_policy(),
    )

    assert strategist.calls == 2

    assert execution.attempt_count == 2

    assert execution.accepted is False

    assert (
        execution.requires_revision
        is True
    )


def test_valid_proposal_does_not_trigger_revision() -> None:
    strategist = SequencedSeasonStrategist(
        create_valid_response(
            target_load=330.0,
        ),
        create_valid_response(
            target_load=330.0,
        ),
    )

    execution = SeasonStrategistService(
        strategist=strategist,
        max_attempts=3,
    ).execute(
        context=create_context(),
        policy=create_policy(),
    )

    assert strategist.calls == 1

    assert execution.attempt_count == 1

    assert execution.accepted is True


def test_invalid_max_attempts_is_rejected() -> None:
    strategist = FakeSeasonStrategist(
        response=create_valid_response(),
    )

    try:
        SeasonStrategistService(
            strategist=strategist,
            max_attempts=0,
        )
    except ValueError as exc:
        assert (
            "tentatives"
            in str(exc)
        )
    else:
        raise AssertionError(
            "Une valeur max_attempts=0 "
            "aurait dû être rejetée."
        )

def test_revision_feedback_is_json_serializable() -> None:
    import json

    strategist = SequencedSeasonStrategist(
        create_valid_response(
            target_load=400.0,
        ),
        create_valid_response(
            target_load=330.0,
        ),
    )

    SeasonStrategistService(
        strategist=strategist,
    ).execute(
        context=create_context(),
        policy=create_policy(),
    )

    revision_request = (
        strategist.requests[1]
    )

    encoded = json.dumps(
        revision_request.instructions,
        ensure_ascii=False,
    )

    assert isinstance(
        encoded,
        str,
    )