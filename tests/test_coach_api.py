from datetime import date, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient

from opencoach.api.app import create_app
from opencoach.api.coach import (
    get_coach_decision_service,
)
from opencoach.api.intervals import (
    get_local_athlete_profile_id,
)
from opencoach.coaching import (
    CoachDecision,
    CoachDecisionAssessment,
    PlannedSessionUnavailableError,
)
from opencoach.coaching.service import (
    CoachSessionDecision,
)

from opencoach.models import (
    TrainingSession,
    WellnessDay,
)
from opencoach.readiness import (
    DailyReadiness,
    MetricBaseline,
    MetricComparison,
    ReadinessAssessment,
    ReadinessBaseline,
    ReadinessComparison,
    ReadinessSignal,
)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from opencoach.training import (
    DailyTrainingLoadService,
    RecentTrainingLoadService,
    TrainingLoadComparisonService,
)

TODAY = date.today()

class FakeCoachDecisionService:
    def __init__(
        self,
        *,
        assessment=None,
        error=None,
    ) -> None:
        self.assessment = assessment
        self.error = error
        self.calls = []

    def calculate(
        self,
        athlete_profile_id,
        target_date,
    ):
        self.calls.append(
            (
                athlete_profile_id,
                target_date,
            )
        )

        if self.error is not None:
            raise self.error

        return self.assessment


def create_assessment() -> CoachDecisionAssessment:
    session = TrainingSession(
        id=uuid4(),
        date=TODAY,
        type="intervals",
        sport_type="Run",
        title="Fractionné",
        description="Séance qualitative.",
        duration_minutes=60,
        distance_km=10.0,
        elevation_gain_m=100.0,
        intensity="high",
        heart_rate_zone="Z4",
        status="planned",
    )

    baseline = ReadinessBaseline(
        start_date=date(
            2026,
            8,
            4,
        ),
        end_date=date(
            2026,
            8,
            17,
        ),
        hrv=MetricBaseline(
            median=52.0,
            sample_count=14,
            reliable=True,
        ),
        resting_hr=MetricBaseline(
            median=46.0,
            sample_count=14,
            reliable=True,
        ),
        sleep_seconds=MetricBaseline(
            median=27000.0,
            sample_count=14,
            reliable=True,
        ),
        sleep_score=MetricBaseline(
            median=80.0,
            sample_count=14,
            reliable=True,
        ),
    )

    comparison = ReadinessComparison(
        hrv=MetricComparison(
            current=50.0,
            baseline=52.0,
            absolute_delta=-2.0,
            percent_delta=-3.8,
            reliable=True,
        ),
        resting_hr=MetricComparison(
            current=47.0,
            baseline=46.0,
            absolute_delta=1.0,
            percent_delta=2.2,
            reliable=True,
        ),
        sleep_seconds=MetricComparison(
            current=25200.0,
            baseline=27000.0,
            absolute_delta=-1800.0,
            percent_delta=-6.7,
            reliable=True,
        ),
        sleep_score=MetricComparison(
            current=78.0,
            baseline=80.0,
            absolute_delta=-2.0,
            percent_delta=-2.5,
            reliable=True,
        ),
    )

    readiness = DailyReadiness(
        score=50.0,
        level="moderate",
        signals=(
            ReadinessSignal(
                metric="hrv",
                level="normal",
                reason=(
                    "HRV -3.8 % par rapport "
                    "à la baseline."
                ),
                current_value=50.0,
                reference_value=52.0,
            ),
            ReadinessSignal(
                metric="sleep_duration",
                level="warning",
                reason=(
                    "Sommeil 7.0 h, "
                    "-6.7 % vs baseline."
                ),
                current_value=25200.0,
                reference_value=27000.0,
            ),
        ),
        warning_count=1,
        critical_count=1,
        training_constraints=(
            "avoid_high_intensity",
            "prefer_recovery_or_rest",
        ),
        fitness_ctl=40.0,
        fatigue_atl=35.0,
        training_balance=5.0,
    )

    readiness_assessment = ReadinessAssessment(
        date=TODAY,
        provider="intervals",
        current=WellnessDay(
            provider="intervals",
            date=TODAY,
            fitness_ctl=40.0,
            fatigue_atl=35.0,
        ),
        baseline=baseline,
        comparison=comparison,
        context=None,
        readiness=readiness,
        source_date=TODAY,
        data_age_days=0,
        data_status="fresh",
    )

    decision = CoachDecision(
        action="reduce",
        reason=(
            "La récupération permet de maintenir "
            "l'entraînement avec une charge réduite."
        ),
        original_duration_minutes=60,
        recommended_duration_minutes=36,
        duration_factor=0.595,
        intensity_factor=0.8,
        original_intensity="high",
        recommended_intensity="easy",
        constraints=(
            "avoid_high_intensity",
            "prefer_recovery_or_rest",
        ),
    )

    return CoachDecisionAssessment(
        date=TODAY,
        session_decisions=(
            CoachSessionDecision(
                session=session,
                decision=decision,
            ),
        ),
        readiness=readiness_assessment,
    )

def create_stale_assessment() -> CoachDecisionAssessment:
    assessment = create_assessment()

    stale_readiness = ReadinessAssessment(
        date=assessment.readiness.date,
        provider=assessment.readiness.provider,
        current=assessment.readiness.current,
        baseline=assessment.readiness.baseline,
        comparison=assessment.readiness.comparison,
        context=assessment.readiness.context,
        readiness=assessment.readiness.readiness,
        source_date=(
            TODAY
            - timedelta(days=1)
        ),
        data_age_days=1,
        data_status="stale",
    )

    return CoachDecisionAssessment(
        date=assessment.date,
        session_decisions=assessment.session_decisions,
        readiness=stale_readiness,
        recent_load=assessment.recent_load,
        recent_load_assessment=(
            assessment.recent_load_assessment
        ),
    )

def create_client(
    service: FakeCoachDecisionService,
):
    app = create_app()

    profile_id = uuid4()

    app.dependency_overrides[
        get_local_athlete_profile_id
    ] = lambda: profile_id

    app.dependency_overrides[
        get_coach_decision_service
    ] = lambda: service

    return (
        TestClient(app),
        profile_id,
    )


def test_coach_api_returns_today_decision() -> None:
    service = FakeCoachDecisionService(
        assessment=create_assessment(),
    )

    client, profile_id = create_client(
        service
    )

    response = client.get(
        "/api/coach/today"
    )

    assert response.status_code == 200

    payload = response.json()

    assert "session_decisions" in payload

    assert isinstance(
        payload["session_decisions"],
        list,
    )

    assert len(
        payload["session_decisions"]
    ) == 1

    assert "signals" in payload["readiness"]

    assert isinstance(
        payload["readiness"]["signals"],
        list,
    )

    assert len(
        payload["readiness"]["signals"]
    ) > 0

    signal = payload["readiness"]["signals"][0]

    assert "metric" in signal
    assert "level" in signal
    assert "reason" in signal
    assert "current_value" in signal
    assert "reference_value" in signal

    assert payload["date"] == (
        TODAY.isoformat()
    )

    assert payload["session_decisions"][0]["session"]["title"] == (
        "Fractionné"
    )

    assert (
        payload["session_decisions"][0]["session"]["duration_minutes"]
        == 60
    )

    assert payload["readiness"]["score"] == 50.0
    assert payload["readiness"]["level"] == "moderate"

    assert (
        payload["readiness"]["source_date"]
        == TODAY.isoformat()
    )

    assert (
        payload["readiness"]["data_age_days"]
        == 0
    )

    assert (
        payload["readiness"]["data_status"]
        == "fresh"
    )

    assert payload["data_warning"] is None

    assert payload["session_decisions"][0]["decision"]["action"] == "reduce"
    assert payload["recent_load"] is None

    assert (
        payload["recent_load_assessment"]
        is None
    )
    assert (
        payload["session_decisions"][0]["decision"][
            "recommended_duration_minutes"
        ]
        == 36
    )

    assert (
        payload["session_decisions"][0]["decision"][
            "recommended_intensity"
        ]
        == "easy"
    )

    assert service.calls == [
        (
            profile_id,
            TODAY,
        )
    ]


def test_coach_api_returns_multiple_session_decisions() -> None:
    from dataclasses import replace

    assessment = create_assessment()

    first_item = assessment.session_decisions[0]

    assert first_item.session is not None

    second_session = replace(
        first_item.session,
        title="Renforcement",
        type="strength",
        sport_type="Strength",
        duration_minutes=30,
        intensity="easy",
        heart_rate_zone=None,
    )

    second_decision = replace(
        first_item.decision,
        original_duration_minutes=30,
        recommended_duration_minutes=30,
        original_intensity="easy",
        recommended_intensity="easy",
    )

    multi_assessment = CoachDecisionAssessment(
        date=assessment.date,
        session_decisions=(
            first_item,
            CoachSessionDecision(
                session=second_session,
                decision=second_decision,
            ),
        ),
        readiness=assessment.readiness,
        recent_load=assessment.recent_load,
        recent_load_assessment=(
            assessment.recent_load_assessment
        ),
    )

    service = FakeCoachDecisionService(
        assessment=multi_assessment,
    )

    client, _ = create_client(service)

    response = client.get(
        "/api/coach/today"
    )

    assert response.status_code == 200

    payload = response.json()

    assert "session_decisions" in payload

    assert len(
        payload["session_decisions"]
    ) == 2

    first = payload["session_decisions"][0]
    second = payload["session_decisions"][1]

    assert first["session"]["title"] == "Fractionné"

    assert (
        first["session"]["duration_minutes"]
        == 60
    )

    assert second["session"]["title"] == "Renforcement"

    assert (
        second["session"]["duration_minutes"]
        == 30
    )

    assert second["session"]["type"] == "strength"
    assert second["session"]["sport_type"] == "Strength"

    assert "decision" in first
    assert "decision" in second

    assert (
        second["decision"][
            "original_duration_minutes"
        ]
        == 30
    )

    assert (
        second["decision"][
            "recommended_duration_minutes"
        ]
        == 30
    )

    # L'ancien contrat mono-séance ne doit plus
    # être exposé au niveau racine.
    assert "session" not in payload
    assert "decision" not in payload


def create_rest_assessment() -> CoachDecisionAssessment:
    assessment = create_assessment()

    decision = CoachDecision(
        action="rest",
        reason=(
            "Aucune séance n'est planifiée aujourd'hui. "
            "Journée de repos maintenue."
        ),
        original_duration_minutes=None,
        recommended_duration_minutes=None,
        duration_factor=None,
        intensity_factor=None,
        original_intensity=None,
        recommended_intensity=None,
        constraints=(),
    )

    return CoachDecisionAssessment(
        date=TODAY,
        session_decisions=(
            CoachSessionDecision(
                session=None,
                decision=decision,
            ),
        ),
        readiness=assessment.readiness,
    )

def test_coach_api_returns_rest_without_planned_session() -> None:
    service = FakeCoachDecisionService(
        assessment=create_rest_assessment(),
    )

    client, _ = create_client(
        service
    )

    response = client.get(
        "/api/coach/today"
    )

    assert response.status_code == 200

    payload = response.json()

    assert "signals" in payload["readiness"]

    assert isinstance(
        payload["readiness"]["signals"],
        list,
    )

    assert len(
        payload["readiness"]["signals"]
    ) > 0

    signal = payload["readiness"]["signals"][0]

    assert "metric" in signal
    assert "level" in signal
    assert "reason" in signal
    assert "current_value" in signal
    assert "reference_value" in signal

    assert len(payload["session_decisions"]) == 1

    assert (
        payload["session_decisions"][0]["session"]
        is None
    )
    assert payload["session_decisions"][0]["decision"]["action"] == "rest"

    assert (
        payload["session_decisions"][0]["decision"][
            "recommended_duration_minutes"
        ]
        is None
    )
def test_coach_api_builds_recent_training_load_dependencies() -> None:
    engine = create_engine(
        "sqlite:///:memory:",
    )

    SessionLocal = sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )

    db = SessionLocal()

    try:
        service = get_coach_decision_service(
            db,
        )

        assert service.recent_load_service is not None

        assert isinstance(
            service.recent_load_service,
            RecentTrainingLoadService,
        )

        comparison_service = (
            service
            .recent_load_service
            .comparison_service
        )

        assert isinstance(
            comparison_service,
            TrainingLoadComparisonService,
        )

        daily_load_service = (
            comparison_service
            .daily_training_load_service
        )

        assert isinstance(
            daily_load_service,
            DailyTrainingLoadService,
        )

        assert (
            daily_load_service
            .training_session_repository
            is service.training_repository
        )

        assert (
            comparison_service
            .training_session_repository
            is service.training_repository
        )

    finally:
        db.close()

def test_coach_api_reports_stale_readiness_data() -> None:
    service = FakeCoachDecisionService(
        assessment=create_stale_assessment(),
    )

    client, _ = create_client(service)

    response = client.get(
        "/api/coach/today"
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["readiness"]["source_date"]
        == (TODAY - timedelta(days=1)).isoformat()
    )

    assert (
        payload["readiness"]["data_age_days"]
        == 1
    )

    assert (
        payload["readiness"]["data_status"]
        == "stale"
    )

    assert payload["data_warning"] is not None

    assert (
        "données de récupération du jour"
        in payload["data_warning"]
    )
