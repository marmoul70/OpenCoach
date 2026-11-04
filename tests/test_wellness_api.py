from datetime import date, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient

from opencoach.api.app import create_app
from opencoach.api.intervals import (
    get_current_athlete_profile_id,
)
from opencoach.api.wellness import (
    get_daily_context_repository,
    get_wellness_repository,
)
from opencoach.database.repositories import (
    WellnessRepositoryError,
)
from opencoach.models import DailyContext, WellnessDay


class FakeWellnessRepository:
    def __init__(
        self,
        wellness: WellnessDay | None = None,
        error: Exception | None = None,
    ) -> None:
        self.wellness = wellness
        self.error = error
        self.calls = []

    def list_range(
        self,
        athlete_profile_id,
        start_date,
        end_date,
        *,
        provider=None,
    ):
        if self.error is not None:
            raise self.error
        if (
            self.wellness is None
            or self.wellness.provider != provider
            or not start_date <= self.wellness.date <= end_date
        ):
            return []
        return [self.wellness]

    def get_latest(
        self,
        athlete_profile_id,
        *,
        provider=None,
    ) -> WellnessDay | None:
        self.calls.append((athlete_profile_id, provider))

        if self.error is not None:
            raise self.error

        if self.wellness is None or (
            provider is not None and self.wellness.provider != provider
        ):
            return None
        return self.wellness


def create_client(
    repository: FakeWellnessRepository,
):
    app = create_app()

    profile_id = uuid4()

    app.dependency_overrides[
        get_current_athlete_profile_id
    ] = lambda: profile_id

    app.dependency_overrides[
        get_wellness_repository
    ] = lambda: repository

    return TestClient(app), profile_id


def test_get_latest_wellness() -> None:
    repository = FakeWellnessRepository(
        WellnessDay(
            provider="intervals",
            date=date(2026, 8, 9),
            fitness_ctl=19.6794,
            fatigue_atl=14.273309,
            ramp_rate=-1.2402077,
            resting_hr=46,
            hrv=52.0,
            sleep_seconds=76140,
            sleep_score=77.0,
            sleep_quality=3,
            avg_sleeping_hr=48.0,
            spo2=99.0,
            steps=34711,
        )
    )

    client, profile_id = create_client(
        repository,
    )

    response = client.get(
        "/api/wellness/latest"
    )

    assert response.status_code == 200

    assert response.json() == {
        "provider": "intervals",
        "date": "2026-08-09",
        "fitness_ctl": 19.6794,
        "fatigue_atl": 14.273309,
        "ramp_rate": -1.2402077,
        "resting_hr": 46,
        "hrv": 52.0,
        "hrv_baseline": None,
        "stress_avg": None,
        "sleep_seconds": 76140,
        "sleep_score": 77.0,
        "sleep_quality": 3,
        "sleep_deep_seconds": None,
        "sleep_light_seconds": None,
        "sleep_rem_seconds": None,
        "sleep_awake_seconds": None,
        "avg_sleeping_hr": 48.0,
        "min_sleeping_hr": None,
        "max_sleeping_hr": None,
        "spo2": 99.0,
        "steps": 34711,
        "provider_updated_at": None,
    }

    assert repository.calls == [
        (profile_id, "coros"),
        (profile_id, "intervals"),
    ]


def test_get_latest_wellness_returns_404_when_empty() -> None:
    repository = FakeWellnessRepository()

    client, _ = create_client(
        repository,
    )

    response = client.get(
        "/api/wellness/latest"
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Aucune donnée Wellness disponible."
    }


def test_get_latest_wellness_handles_storage_error() -> None:
    repository = FakeWellnessRepository(
        error=WellnessRepositoryError(
            "database failure"
        ),
    )

    client, _ = create_client(
        repository,
    )

    response = client.get(
        "/api/wellness/latest"
    )

    assert response.status_code == 503

    assert response.json() == {
        "detail": (
            "Impossible de charger les données Wellness."
        )
    }


def test_get_latest_wellness_prefers_coros_when_available() -> None:
    repository = FakeWellnessRepository(
        WellnessDay(
            provider="coros",
            date=date(2026, 11, 4),
            hrv=45.0,
            hrv_baseline=42.0,
            stress_avg=28.0,
            sleep_deep_seconds=7200,
        )
    )
    client, profile_id = create_client(repository)

    response = client.get("/api/wellness/latest")

    assert response.status_code == 200
    assert response.json()["provider"] == "coros"
    assert response.json()["hrv_baseline"] == 42.0
    assert response.json()["stress_avg"] == 28.0
    assert response.json()["sleep_deep_seconds"] == 7200
    assert repository.calls == [
        (profile_id, "coros"),
        (profile_id, "intervals"),
    ]



class FakeDailyContextRepository:
    def __init__(self, context=None):
        self.context = context

    def get_by_date(self, athlete_profile_id, context_date):
        if self.context is not None and self.context.date == context_date:
            return self.context
        return None


def test_get_recovery_assessment_exposes_windows_and_subjective_fatigue() -> None:
    target = date.today()
    repository = FakeWellnessRepository(
        WellnessDay(
            provider="coros",
            date=target,
            hrv=46.0,
            hrv_baseline=43.0,
            resting_hr=48,
            stress_avg=25.0,
            sleep_seconds=7 * 3600,
            fatigue_atl=32.0,
            fitness_ctl=40.0,
        )
    )
    context_repository = FakeDailyContextRepository(
        DailyContext(
            date=target,
            fatigue_subjective=3,
            pain_level=1,
            illness_status="none",
            treatment_impact="none",
            motivation=4,
        )
    )
    client, _ = create_client(repository)
    client.app.dependency_overrides[
        get_daily_context_repository
    ] = lambda: context_repository

    response = client.get("/api/wellness/recovery")

    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "coros"
    assert payload["data_status"] == "fresh"
    assert [item["days"] for item in payload["windows"]] == [7, 14, 30]
    assert payload["windows"][0]["metrics"]["hrv"]["current"] == 46.0
    assert payload["windows"][0]["metrics"]["hrv"]["sample_count"] == 1
    assert payload["windows"][0]["metrics"]["stress_avg"]["current"] == 25.0
    assert payload["subjective"]["fatigue"] == 3
    assert payload["subjective"]["pain"] == 1


def test_get_recovery_assessment_returns_unavailable_when_no_sensor_data() -> None:
    client, _ = create_client(FakeWellnessRepository())
    client.app.dependency_overrides[
        get_daily_context_repository
    ] = lambda: FakeDailyContextRepository()

    response = client.get("/api/wellness/recovery")

    assert response.status_code == 200
    payload = response.json()
    assert payload["data_status"] == "unavailable"
    assert payload["source_date"] is None
    assert payload["windows"][0]["metrics"]["hrv"]["current"] is None
    assert payload["subjective"] is None
