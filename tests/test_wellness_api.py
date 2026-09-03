from datetime import date
from uuid import uuid4

from fastapi.testclient import TestClient

from opencoach.api.app import create_app
from opencoach.api.intervals import (
    get_current_athlete_profile_id,
)
from opencoach.api.wellness import (
    get_wellness_repository,
)
from opencoach.database.repositories import (
    WellnessRepositoryError,
)
from opencoach.models import WellnessDay


class FakeWellnessRepository:
    def __init__(
        self,
        wellness: WellnessDay | None = None,
        error: Exception | None = None,
    ) -> None:
        self.wellness = wellness
        self.error = error
        self.calls = []

    def get_latest(
        self,
        athlete_profile_id,
    ) -> WellnessDay | None:
        self.calls.append(
            athlete_profile_id,
        )

        if self.error is not None:
            raise self.error

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
        "sleep_seconds": 76140,
        "sleep_score": 77.0,
        "sleep_quality": 3,
        "avg_sleeping_hr": 48.0,
        "spo2": 99.0,
        "steps": 34711,
        "provider_updated_at": None,
    }

    assert repository.calls == [
        profile_id,
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
