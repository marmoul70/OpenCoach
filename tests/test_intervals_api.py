from uuid import uuid4

from fastapi.testclient import TestClient

from opencoach.api.app import create_app
from opencoach.api.intervals import (
    get_intervals_application_service,
    get_local_athlete_profile_id,
)
from opencoach.database.repositories import ActivityRepositoryError
from opencoach.integrations.intervals import (
    IntervalsApiError,
    IntervalsAuthenticationError,
    IntervalsDataError,
)


class FakeIntervalsApplicationService:
    def __init__(
        self,
        *,
        result: int = 0,
        error: Exception | None = None,
    ) -> None:
        self.result = result
        self.error = error
        self.calls = []

    def sync_activities(
        self,
        athlete_profile_id,
        *,
        newest=None,
        days=30,
    ) -> int:
        self.calls.append(
            (
                athlete_profile_id,
                newest,
                days,
            )
        )

        if self.error is not None:
            raise self.error

        return self.result


def create_test_client(
    service: FakeIntervalsApplicationService,
):
    app = create_app()

    profile_id = uuid4()

    app.dependency_overrides[
        get_local_athlete_profile_id
    ] = lambda: profile_id

    app.dependency_overrides[
        get_intervals_application_service
    ] = lambda: service

    return TestClient(app), profile_id


def test_sync_intervals_activities() -> None:
    service = FakeIntervalsApplicationService(
        result=21,
    )

    client, profile_id = create_test_client(
        service,
    )

    response = client.post(
        "/api/integrations/intervals/sync"
    )

    assert response.status_code == 200

    assert response.json() == {
        "provider": "intervals",
        "synced_activities": 21,
        "days": 30,
    }

    assert service.calls == [
        (
            profile_id,
            None,
            30,
        )
    ]


def test_sync_intervals_accepts_custom_period() -> None:
    service = FakeIntervalsApplicationService(
        result=50,
    )

    client, profile_id = create_test_client(
        service,
    )

    response = client.post(
        "/api/integrations/intervals/sync?days=90"
    )

    assert response.status_code == 200

    assert response.json() == {
        "provider": "intervals",
        "synced_activities": 50,
        "days": 90,
    }

    assert service.calls == [
        (
            profile_id,
            None,
            90,
        )
    ]


def test_sync_intervals_rejects_invalid_period() -> None:
    service = FakeIntervalsApplicationService()

    client, _ = create_test_client(
        service,
    )

    response = client.post(
        "/api/integrations/intervals/sync?days=0"
    )

    assert response.status_code == 422
    assert service.calls == []


def test_sync_intervals_handles_authentication_error() -> None:
    service = FakeIntervalsApplicationService(
        error=IntervalsAuthenticationError(
            "authentication failed"
        ),
    )

    client, _ = create_test_client(
        service,
    )

    response = client.post(
        "/api/integrations/intervals/sync"
    )

    assert response.status_code == 502

    assert response.json() == {
        "detail": (
            "L'authentification auprès d'Intervals.icu a échoué."
        )
    }


def test_sync_intervals_handles_api_error() -> None:
    service = FakeIntervalsApplicationService(
        error=IntervalsApiError(
            "api failed"
        ),
    )

    client, _ = create_test_client(
        service,
    )

    response = client.post(
        "/api/integrations/intervals/sync"
    )

    assert response.status_code == 502

    assert response.json() == {
        "detail": "Intervals.icu est temporairement indisponible."
    }


def test_sync_intervals_handles_invalid_data() -> None:
    service = FakeIntervalsApplicationService(
        error=IntervalsDataError(
            "invalid data"
        ),
    )

    client, _ = create_test_client(
        service,
    )

    response = client.post(
        "/api/integrations/intervals/sync"
    )

    assert response.status_code == 502

    assert response.json() == {
        "detail": "Intervals.icu a retourné des données invalides."
    }


def test_sync_intervals_handles_storage_error() -> None:
    service = FakeIntervalsApplicationService(
        error=ActivityRepositoryError(
            "storage failed"
        ),
    )

    client, _ = create_test_client(
        service,
    )

    response = client.post(
        "/api/integrations/intervals/sync"
    )

    assert response.status_code == 503

    assert response.json() == {
        "detail": "Impossible d'enregistrer les activités."
    }