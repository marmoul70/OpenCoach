from __future__ import annotations

import json

import httpx
import pytest

from opencoach.integrations.intervals.client import (
    IntervalsClient,
)


def create_client(
    handler,
) -> IntervalsClient:
    return IntervalsClient(
        api_key="secret",
        athlete_id="athlete-test",
        transport=httpx.MockTransport(
            handler,
        ),
    )


def test_get_activity_details_requests_intervals() -> None:
    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        assert (
            request.url.path
            == "/api/v1/activity/i123"
        )

        assert (
            request.url.params["intervals"]
            == "true"
        )

        return httpx.Response(
            200,
            json={
                "id": "i123",
                "icu_intervals": [
                    {
                        "type": "WORK",
                        "start_index": 100,
                        "end_index": 200,
                        "distance": 800.0,
                    },
                ],
            },
        )

    client = create_client(
        handler,
    )

    result = client.get_activity_details(
        "i123",
    )

    assert result["id"] == "i123"
    assert len(result["icu_intervals"]) == 1


def test_get_activity_details_can_disable_intervals() -> None:
    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        assert (
            request.url.params["intervals"]
            == "false"
        )

        return httpx.Response(
            200,
            json={
                "id": "i123",
            },
        )

    client = create_client(
        handler,
    )

    result = client.get_activity_details(
        "i123",
        include_intervals=False,
    )

    assert result == {
        "id": "i123",
    }


def test_get_activity_streams_requests_only_coach_streams() -> None:
    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        assert (
            request.url.path
            == "/api/v1/activity/i123/streams.json"
        )

        assert (
            request.url.params["types"]
            == (
                "time,distance,heartrate,"
                "velocity_smooth,cadence,watts"
            )
        )

        return httpx.Response(
            200,
            json=[
                {
                    "type": "time",
                    "data": [
                        0,
                        1,
                        2,
                    ],
                },
                {
                    "type": "heartrate",
                    "data": [
                        120,
                        125,
                        130,
                    ],
                },
            ],
        )

    client = create_client(
        handler,
    )

    result = client.get_activity_streams(
        "i123",
    )

    assert len(result) == 2
    assert result[0]["type"] == "time"
    assert result[1]["type"] == "heartrate"


def test_get_activity_streams_accepts_selected_types() -> None:
    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        assert (
            request.url.params["types"]
            == "time,heartrate"
        )

        return httpx.Response(
            200,
            json=[
                {
                    "type": "time",
                    "data": [
                        0,
                        1,
                    ],
                },
            ],
        )

    client = create_client(
        handler,
    )

    result = client.get_activity_streams(
        "i123",
        types=(
            "time",
            "heartrate",
        ),
    )

    assert result[0]["type"] == "time"


def test_activity_detail_rejects_empty_activity_id() -> None:
    client = create_client(
        lambda request: httpx.Response(
            500,
        ),
    )

    with pytest.raises(
        ValueError,
        match="identifiant d'activité",
    ):
        client.get_activity_details(
            "   ",
        )


def test_activity_streams_reject_empty_activity_id() -> None:
    client = create_client(
        lambda request: httpx.Response(
            500,
        ),
    )

    with pytest.raises(
        ValueError,
        match="identifiant d'activité",
    ):
        client.get_activity_streams(
            "",
        )


def test_activity_streams_reject_empty_types() -> None:
    client = create_client(
        lambda request: httpx.Response(
            500,
        ),
    )

    with pytest.raises(
        ValueError,
        match="Au moins un type",
    ):
        client.get_activity_streams(
            "i123",
            types=(),
        )


def test_activity_details_requires_json_object() -> None:
    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            200,
            content=json.dumps(
                [
                    {
                        "id": "i123",
                    },
                ],
            ),
            headers={
                "content-type": "application/json",
            },
        )

    client = create_client(
        handler,
    )

    with pytest.raises(
        Exception,
        match="Réponse Intervals.icu inattendue",
    ):
        client.get_activity_details(
            "i123",
        )


def test_activity_streams_requires_json_list() -> None:
    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "type": "time",
                "data": [],
            },
        )

    client = create_client(
        handler,
    )

    with pytest.raises(
        Exception,
        match="Réponse Intervals.icu inattendue",
    ):
        client.get_activity_streams(
            "i123",
        )
