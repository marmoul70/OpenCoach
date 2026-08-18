from datetime import date
from uuid import uuid4

from fastapi.testclient import TestClient

from opencoach.api.app import create_app
from opencoach.api.intervals import (
    get_local_athlete_profile_id,
)
from opencoach.api.readiness import (
    get_readiness_service,
)
from opencoach.models import WellnessDay
from opencoach.readiness import (
    DailyReadiness,
    MetricBaseline,
    MetricComparison,
    ReadinessAssessment,
    ReadinessBaseline,
    ReadinessComparison,
    ReadinessDataUnavailableError,
    ReadinessSignal,
)


TODAY = date.today()


class FakeReadinessService:
    def __init__(
        self,
        result=None,
        error=None,
    ) -> None:
        self.result = result
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

        return self.result


def create_assessment() -> ReadinessAssessment:
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
        score=100.0,
        level="high",

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
        ),

        warning_count=0,
        critical_count=0,

        training_constraints=(),

        fitness_ctl=40.0,
        fatigue_atl=35.0,
        training_balance=5.0,
    )

    return ReadinessAssessment(
        date=TODAY,
        provider="intervals",

        current=WellnessDay(
            provider="intervals",
            date=TODAY,
            fitness_ctl=40.0,
            fatigue_atl=35.0,
            hrv=50.0,
            resting_hr=47,
            sleep_seconds=25200,
            sleep_score=78.0,
        ),

        baseline=baseline,
        comparison=comparison,
        context=None,
        readiness=readiness,
)


def create_client(
    service: FakeReadinessService,
):
    app = create_app()

    profile_id = uuid4()

    app.dependency_overrides[
        get_local_athlete_profile_id
    ] = lambda: profile_id

    app.dependency_overrides[
        get_readiness_service
    ] = lambda: service

    return (
        TestClient(app),
        profile_id,
    )


def test_readiness_api_returns_today_assessment() -> None:
    service = FakeReadinessService(
        result=create_assessment(),
    )

    client, profile_id = create_client(
        service
    )

    response = client.get(
        "/api/readiness/today"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["provider"] == "intervals"

    assert payload["readiness"]["score"] == 100.0
    assert payload["readiness"]["level"] == "high"

    assert payload["baseline"]["hrv"]["median"] == 52.0

    assert (
        payload["comparison"]["hrv"]["percent_delta"]
        == -3.8
    )

    assert service.calls == [
        (
            profile_id,
            TODAY,
        )
    ]


def test_readiness_api_returns_404_when_data_missing() -> None:
    service = FakeReadinessService(
        error=ReadinessDataUnavailableError(
            "Aucune donnée Wellness disponible."
        )
    )

    client, _ = create_client(
        service
    )

    response = client.get(
        "/api/readiness/today"
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": (
            "Aucune donnée Wellness disponible."
        )
    }
