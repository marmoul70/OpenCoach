from datetime import datetime
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from opencoach.api.app import create_app
from opencoach.api.intervals import (
    get_integration_connection_service,
    get_intervals_application_service,
    get_local_athlete_profile_id,
)
from opencoach.database.repositories import (
    ActivityRepositoryError,
    WellnessRepositoryError,
)
from opencoach.integrations.intervals import (
    IntervalsApiError,
    IntervalsAuthenticationError,
    IntervalsDataError,
)
from opencoach.models import IntegrationConnection
from opencoach.services import (
    IntegrationConnectionServiceError,
)

import opencoach.api.intervals as intervals_api

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

    def sync_all(
        self,
        athlete_profile_id,
        *,
        newest=None,
        days=30,
    ) -> tuple[int, int]:
        self.calls.append(
            (
                athlete_profile_id,
                newest,
                days,
            )
        )

        if self.error is not None:
            raise self.error

        return (
            self.result,
            self.result,
        )

class FakeIntegrationConnectionService:
    def __init__(
        self,
        connection=None,
        *,
        error=None,
    ) -> None:
        self.connection = connection
        self.error = error
        self.saved = None

        self.synced_calls: list[
            tuple[
                UUID,
                str,
                datetime,
            ]
        ] = []

    def get_connection(
        self,
        athlete_profile_id,
        provider,
    ):
        if self.error is not None:
            raise self.error

        return self.connection

    def save_intervals_connection(
        self,
        athlete_profile_id,
        athlete_id,
        api_key,
        *,
        enabled=True,
    ):
        if self.error is not None:
            raise self.error

        self.saved = {
            "athlete_profile_id":
                athlete_profile_id,
            "athlete_id":
                athlete_id,
            "api_key":
                api_key,
            "enabled":
                enabled,
        }

        connection = IntegrationConnection(
            provider="intervals",
            enabled=enabled,
            athlete_id=athlete_id,
            secret_configured=True,
            last_synced_at=None,
        )

        self.connection = connection

        return connection

    def mark_synced(
        self,
        athlete_profile_id: UUID,
        provider: str,
        synced_at: datetime,
    ) -> None:
        if self.error is not None:
            raise self.error

        self.synced_calls.append(
            (
                athlete_profile_id,
                provider,
                synced_at,
            )
        )

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

    connection_service = (
        FakeIntegrationConnectionService()
    )

    app.dependency_overrides[
        get_integration_connection_service
    ] = lambda: connection_service

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

    payload = response.json()

    assert payload["provider"] == "intervals"
    assert payload["synced_activities"] == 21
    assert payload["synced_wellness_days"] == 21
    assert payload["days"] == 30

    assert isinstance(
        payload["synced_at"],
        str,
    )

    datetime.fromisoformat(
        payload["synced_at"],
    )

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

    payload = response.json()

    assert payload["provider"] == "intervals"
    assert payload["synced_activities"] == 50
    assert payload["synced_wellness_days"] == 50
    assert payload["days"] == 90

    assert isinstance(
        payload["synced_at"],
        str,
    )

    datetime.fromisoformat(
        payload["synced_at"],
    )

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

def test_sync_intervals_handles_wellness_storage_error() -> None:
    service = FakeIntervalsApplicationService(
        error=WellnessRepositoryError(
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
        "detail": (
            "Impossible d'enregistrer les données Wellness."
        )
    }

def test_get_intervals_connection_returns_configured() -> None:
    app = create_app()

    profile_id = uuid4()

    service = FakeIntegrationConnectionService(
        IntegrationConnection(
            provider="intervals",
            enabled=True,
            athlete_id="i651743",
            secret_configured=True,
            last_synced_at=datetime(
                2026,
                8,
                19,
                18,
                30,
            ),
        )
    )

    app.dependency_overrides[
        get_local_athlete_profile_id
    ] = lambda: profile_id

    app.dependency_overrides[
        get_integration_connection_service
    ] = lambda: service

    client = TestClient(app)

    response = client.get(
        "/api/integrations/intervals/connection"
    )

    assert response.status_code == 200

    assert response.json() == {
        "provider": "intervals",
        "configured": True,
        "enabled": True,
        "athlete_id": "i651743",
        "api_key_configured": True,
        "last_synced_at": "2026-08-19T18:30:00",
    }


def test_get_intervals_connection_returns_unconfigured() -> None:
    app = create_app()

    app.dependency_overrides[
        get_local_athlete_profile_id
    ] = lambda: uuid4()

    app.dependency_overrides[
        get_integration_connection_service
    ] = lambda: FakeIntegrationConnectionService()

    client = TestClient(app)

    response = client.get(
        "/api/integrations/intervals/connection"
    )

    assert response.status_code == 200

    assert response.json() == {
        "provider": "intervals",
        "configured": False,
        "enabled": False,
        "athlete_id": None,
        "api_key_configured": False,
        "last_synced_at": None,
    }


def test_put_intervals_connection() -> None:
    app = create_app()

    profile_id = uuid4()
    service = FakeIntegrationConnectionService()

    app.dependency_overrides[
        get_local_athlete_profile_id
    ] = lambda: profile_id

    app.dependency_overrides[
        get_integration_connection_service
    ] = lambda: service

    client = TestClient(app)

    response = client.put(
        "/api/integrations/intervals/connection",
        json={
            "athlete_id": "i651743",
            "api_key": "secret-api-key",
            "enabled": True,
        },
    )

    assert response.status_code == 200

    assert service.saved == {
        "athlete_profile_id": profile_id,
        "athlete_id": "i651743",
        "api_key": "secret-api-key",
        "enabled": True,
    }

    assert response.json() == {
        "provider": "intervals",
        "configured": True,
        "enabled": True,
        "athlete_id": "i651743",
        "api_key_configured": True,
        "last_synced_at": None,
    }


def test_put_intervals_connection_handles_validation_error() -> None:
    app = create_app()

    service = FakeIntegrationConnectionService(
        error=IntegrationConnectionServiceError(
            "La clé API Intervals.icu est obligatoire."
        )
    )

    app.dependency_overrides[
        get_local_athlete_profile_id
    ] = lambda: uuid4()

    app.dependency_overrides[
        get_integration_connection_service
    ] = lambda: service

    client = TestClient(app)

    response = client.put(
        "/api/integrations/intervals/connection",
        json={
            "athlete_id": "i651743",
            "api_key": None,
            "enabled": True,
        },
    )

    assert response.status_code == 422

def test_intervals_connection_test_succeeds(
    monkeypatch,
) -> None:
    class FakeIntervalsClient:
        def __init__(
            self,
            api_key,
            athlete_id,
        ) -> None:
            self.api_key = api_key
            self.athlete_id = athlete_id

        def get_wellness(
            self,
            oldest,
            newest,
        ):
            return []

    monkeypatch.setattr(
        intervals_api,
        "IntervalsClient",
        FakeIntervalsClient,
    )

    client = TestClient(
        create_app()
    )

    response = client.post(
        "/api/integrations/intervals/connection/test",
        json={
            "athlete_id": "i651743",
            "api_key": "secret-api-key",
        },
    )

    assert response.status_code == 200

    assert response.json() == {
        "provider": "intervals",
        "connected": True,
        "athlete_id": "i651743",
    }


def test_intervals_connection_test_rejects_bad_credentials(
    monkeypatch,
) -> None:
    class FakeIntervalsClient:
        def __init__(
            self,
            api_key,
            athlete_id,
        ) -> None:
            pass

        def get_wellness(
            self,
            oldest,
            newest,
        ):
            raise IntervalsAuthenticationError(
                "Authentication failed."
            )

    monkeypatch.setattr(
        intervals_api,
        "IntervalsClient",
        FakeIntervalsClient,
    )

    client = TestClient(
        create_app()
    )

    response = client.post(
        "/api/integrations/intervals/connection/test",
        json={
            "athlete_id": "i651743",
            "api_key": "bad-api-key",
        },
    )

    assert response.status_code == 401

    assert response.json() == {
        "detail": "Identifiants Intervals.icu refusés."
    }

def test_saved_intervals_connection_succeeds(
    monkeypatch,
) -> None:
    app = create_app()

    profile_id = uuid4()

    class FakeCredentials:
        provider = "intervals"
        athlete_id = "i651743"
        secret = "secret-api-key"

    class FakeConnectionService:
        def get_credentials(
            self,
            athlete_profile_id,
            provider,
        ):
            assert athlete_profile_id == profile_id
            assert provider == "intervals"

            return FakeCredentials()

    class FakeIntervalsClient:
        def __init__(
            self,
            api_key,
            athlete_id,
        ) -> None:
            assert api_key == "secret-api-key"
            assert athlete_id == "i651743"

        def get_wellness(
            self,
            oldest,
            newest,
        ):
            return []

    app.dependency_overrides[
        get_local_athlete_profile_id
    ] = lambda: profile_id

    app.dependency_overrides[
        get_integration_connection_service
    ] = lambda: FakeConnectionService()

    monkeypatch.setattr(
        intervals_api,
        "IntervalsClient",
        FakeIntervalsClient,
    )

    client = TestClient(app)

    response = client.post(
        "/api/integrations/intervals/connection/test-saved"
    )

    assert response.status_code == 200

    assert response.json() == {
        "provider": "intervals",
        "connected": True,
        "athlete_id": "i651743",
    }


def test_saved_intervals_connection_rejects_bad_credentials(
    monkeypatch,
) -> None:
    app = create_app()

    class FakeCredentials:
        provider = "intervals"
        athlete_id = "i651743"
        secret = "bad-api-key"

    class FakeConnectionService:
        def get_credentials(
            self,
            athlete_profile_id,
            provider,
        ):
            return FakeCredentials()

    class FakeIntervalsClient:
        def __init__(
            self,
            api_key,
            athlete_id,
        ) -> None:
            pass

        def get_wellness(
            self,
            oldest,
            newest,
        ):
            raise IntervalsAuthenticationError(
                "Authentication failed."
            )

    app.dependency_overrides[
        get_local_athlete_profile_id
    ] = lambda: uuid4()

    app.dependency_overrides[
        get_integration_connection_service
    ] = lambda: FakeConnectionService()

    monkeypatch.setattr(
        intervals_api,
        "IntervalsClient",
        FakeIntervalsClient,
    )

    client = TestClient(app)

    response = client.post(
        "/api/integrations/intervals/connection/test-saved"
    )

    assert response.status_code == 401

    assert response.json() == {
        "detail": "Identifiants Intervals.icu refusés."
    }