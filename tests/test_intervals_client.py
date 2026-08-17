from datetime import date

import httpx
import pytest

from opencoach.integrations.intervals import (
    IntervalsApiError,
    IntervalsAuthenticationError,
    IntervalsClient,
)


def create_client(
    handler,
) -> IntervalsClient:
    transport = httpx.MockTransport(handler)

    return IntervalsClient(
        api_key="test-api-key",
        athlete_id="i123456",
        transport=transport,
    )


def test_get_activities_returns_api_data() -> None:
    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == (
            "/api/v1/athlete/i123456/activities"
        )

        assert request.url.params["oldest"] == "2026-08-01"
        assert request.url.params["newest"] == "2026-08-17"

        return httpx.Response(
            200,
            json=[
                {
                    "id": "i176833761",
                    "name": "Morning Course à pied",
                    "type": "Run",
                    "source": "SUUNTO",
                }
            ],
        )

    client = create_client(handler)

    activities = client.get_activities(
        date(2026, 8, 1),
        date(2026, 8, 17),
    )

    assert len(activities) == 1
    assert activities[0]["id"] == "i176833761"
    assert activities[0]["source"] == "SUUNTO"


def test_get_wellness_returns_api_data() -> None:
    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        assert request.url.path == (
            "/api/v1/athlete/i123456/wellness"
        )

        return httpx.Response(
            200,
            json=[
                {
                    "id": "2026-08-17",
                    "ctl": 20.0,
                    "atl": 15.0,
                    "hrv": 42.0,
                }
            ],
        )

    client = create_client(handler)

    wellness = client.get_wellness(
        date(2026, 8, 1),
        date(2026, 8, 17),
    )

    assert len(wellness) == 1
    assert wellness[0]["id"] == "2026-08-17"
    assert wellness[0]["hrv"] == 42.0


@pytest.mark.parametrize(
    "status_code",
    [401, 403],
)
def test_authentication_failure_raises_specific_error(
    status_code: int,
) -> None:
    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            status_code,
            request=request,
        )

    client = create_client(handler)

    with pytest.raises(
        IntervalsAuthenticationError,
        match="Authentification Intervals.icu refusée",
    ):
        client.get_activities(
            date(2026, 8, 1),
            date(2026, 8, 17),
        )


def test_http_error_raises_api_error() -> None:
    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            500,
            request=request,
        )

    client = create_client(handler)

    with pytest.raises(
        IntervalsApiError,
        match="HTTP 500",
    ):
        client.get_activities(
            date(2026, 8, 1),
            date(2026, 8, 17),
        )


def test_network_error_raises_api_error() -> None:
    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        raise httpx.ConnectError(
            "connection failed",
            request=request,
        )

    client = create_client(handler)

    with pytest.raises(
        IntervalsApiError,
        match="Impossible de contacter Intervals.icu",
    ):
        client.get_activities(
            date(2026, 8, 1),
            date(2026, 8, 17),
        )


def test_invalid_json_raises_api_error() -> None:
    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            200,
            content=b"not-json",
            request=request,
        )

    client = create_client(handler)

    with pytest.raises(
        IntervalsApiError,
        match="Réponse JSON Intervals.icu invalide",
    ):
        client.get_wellness(
            date(2026, 8, 1),
            date(2026, 8, 17),
        )


def test_unexpected_response_type_raises_api_error() -> None:
    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "unexpected": "object",
            },
            request=request,
        )

    client = create_client(handler)

    with pytest.raises(
        IntervalsApiError,
        match="Réponse Intervals.icu inattendue",
    ):
        client.get_wellness(
            date(2026, 8, 1),
            date(2026, 8, 17),
        )


def test_api_key_is_required() -> None:
    with pytest.raises(
        ValueError,
        match="clé API Intervals.icu",
    ):
        IntervalsClient(
            api_key="",
            athlete_id="i123456",
        )


def test_athlete_id_is_required() -> None:
    with pytest.raises(
        ValueError,
        match="identifiant athlète Intervals.icu",
    ):
        IntervalsClient(
            api_key="test-api-key",
            athlete_id="",
        )