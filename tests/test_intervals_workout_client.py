import base64
import json

import httpx
import pytest

from opencoach.integrations.intervals.client import (
    IntervalsClient,
)
from opencoach.integrations.intervals.errors import (
    IntervalsApiError,
    IntervalsAuthenticationError,
    IntervalsDataError,
)


def create_client(handler) -> IntervalsClient:
    return IntervalsClient(
        api_key="secret",
        athlete_id="i123456",
        transport=httpx.MockTransport(
            handler
        ),
    )


def assert_basic_auth(
    request: httpx.Request,
) -> None:
    expected = base64.b64encode(
        b"API_KEY:secret"
    ).decode()

    assert request.headers[
        "Authorization"
    ] == f"Basic {expected}"


def test_bulk_upsert_sends_expected_request():
    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        assert request.method == "POST"

        assert request.url.path == (
            "/api/v1/athlete/"
            "i123456/events/bulk"
        )

        assert (
            request.url.params["upsert"]
            == "true"
        )

        assert_basic_auth(request)

        body = json.loads(
            request.content
        )

        assert body == [
            {
                "external_id":
                    "opencoach:session:abc",
                "category": "WORKOUT",
                "start_date_local":
                    "2026-09-08T00:00:00",
                "type": "Run",
                "name": "Endurance",
                "description":
                    "- 45m 129-152bpm HR",
            }
        ]

        return httpx.Response(
            200,
            json=[
                {
                    "id": 987654,
                    "external_id":
                        "opencoach:session:abc",
                    "category": "WORKOUT",
                }
            ],
        )

    client = create_client(handler)

    result = client.upsert_workouts(
        [
            {
                "external_id":
                    "opencoach:session:abc",
                "category": "WORKOUT",
                "start_date_local":
                    "2026-09-08T00:00:00",
                "type": "Run",
                "name": "Endurance",
                "description":
                    "- 45m 129-152bpm HR",
            }
        ]
    )

    assert result == [
        {
            "id": 987654,
            "external_id":
                "opencoach:session:abc",
            "category": "WORKOUT",
        }
    ]


def test_empty_bulk_upsert_does_not_call_api():
    calls = []

    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        calls.append(request)

        return httpx.Response(
            500
        )

    client = create_client(handler)

    assert client.upsert_workouts([]) == []
    assert calls == []


def test_bulk_delete_uses_external_ids():
    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        assert request.method == "PUT"

        assert request.url.path == (
            "/api/v1/athlete/"
            "i123456/events/bulk-delete"
        )

        assert_basic_auth(request)

        assert json.loads(
            request.content
        ) == [
            {
                "external_id":
                    "opencoach:session:one",
            },
            {
                "external_id":
                    "opencoach:session:two",
            },
        ]

        return httpx.Response(
            200,
            json=2,
        )

    client = create_client(handler)

    result = client.delete_workouts(
        [
            "opencoach:session:one",
            "opencoach:session:two",
        ]
    )

    assert result == 2


def test_empty_bulk_delete_does_not_call_api():
    calls = []

    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        calls.append(request)

        return httpx.Response(
            500
        )

    client = create_client(handler)

    assert client.delete_workouts([]) == 0
    assert calls == []


def test_authentication_error_is_preserved():
    client = create_client(
        lambda request: httpx.Response(
            401
        )
    )

    with pytest.raises(
        IntervalsAuthenticationError
    ):
        client.upsert_workouts(
            [
                {
                    "external_id":
                        "opencoach:session:test",
                }
            ]
        )


def test_server_error_is_intervals_api_error():
    client = create_client(
        lambda request: httpx.Response(
            500
        )
    )

    with pytest.raises(
        IntervalsApiError
    ):
        client.upsert_workouts(
            [
                {
                    "external_id":
                        "opencoach:session:test",
                }
            ]
        )


def test_upsert_rejects_non_list_response():
    client = create_client(
        lambda request: httpx.Response(
            200,
            json={
                "unexpected": True,
            },
        )
    )

    with pytest.raises(
        IntervalsDataError
    ):
        client.upsert_workouts(
            [
                {
                    "external_id":
                        "opencoach:session:test",
                }
            ]
        )


def test_delete_rejects_invalid_response():
    client = create_client(
        lambda request: httpx.Response(
            200,
            json={
                "deleted": 1,
            },
        )
    )

    with pytest.raises(
        IntervalsDataError
    ):
        client.delete_workouts(
            [
                "opencoach:session:test",
            ]
        )


def test_invalid_json_is_data_error():
    client = create_client(
        lambda request: httpx.Response(
            200,
            content=b"not-json",
        )
    )

    with pytest.raises(
        IntervalsDataError
    ):
        client.upsert_workouts(
            [
                {
                    "external_id":
                        "opencoach:session:test",
                }
            ]
        )
