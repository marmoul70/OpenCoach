from datetime import date
from uuid import uuid4

import pytest

from opencoach.integrations.intervals.sync import (
    COACH_STREAM_TYPES,
    IntervalsSyncService,
)
from opencoach.models import ActivityDetail


class FakeClient:
    def __init__(self) -> None:
        self.calls = []

    def get_activities(
        self,
        oldest,
        newest,
    ):
        self.calls.append(
            ("activities", oldest, newest)
        )

        return [
            {
                "id": "i123",
                "name": "Fractionné",
                "type": "Run",
                "start_date": (
                    "2026-08-28T10:00:00Z"
                ),
            },
        ]

    def get_activity_details(
        self,
        activity_id,
        *,
        include_intervals=True,
    ):
        self.calls.append(
            (
                "details",
                activity_id,
                include_intervals,
            )
        )

        return {
            "id": activity_id,

            "stream_types": [

                "time",

                "distance",

                "heartrate",

                "velocity_smooth",

                "cadence",

                "watts",

                "latlng",

            ],
            "icu_lap_count": 2,
            "interval_summary": [
                "2x 3m20s 160bpm",
            ],
            "icu_intervals": [
                {
                    "id": 1,
                    "type": "WORK",
                    "label": None,
                    "start_index": 0,
                    "end_index": 200,
                    "start_time": 0,
                    "end_time": 200,
                    "distance": 800.0,
                    "moving_time": 200,
                    "elapsed_time": 200,
                    "average_speed": 4.0,
                    "average_heartrate": 160,
                    "max_heartrate": 170,
                    "average_cadence": 92.0,
                    "total_elevation_gain": 1.0,
                    "training_load": None,
                },
            ],
        }

    def get_activity_streams(
        self,
        activity_id,
        *,
        types,
    ):
        self.calls.append(
            (
                "streams",
                activity_id,
                types,
            )
        )

        return [
            {
                "type": "time",
                "data": [0, 1, 2],
            },
            {
                "type": "heartrate",
                "data": [150, 155, 160],
            },
            {
                "type": "distance",
                "data": [0.0, 4.0, 8.0],
            },
        ]


class FakeActivityRepository:
    def __init__(self) -> None:
        self.saved = []

    def save_activity(
        self,
        athlete_profile_id,
        activity,
    ) -> None:
        self.saved.append(
            (
                athlete_profile_id,
                activity,
            )
        )


class FakeActivityDetailRepository:
    def __init__(self) -> None:
        self.saved = []

    def save_activity_detail(
        self,
        athlete_profile_id,
        detail,
    ) -> None:
        self.saved.append(
            (
                athlete_profile_id,
                detail,
            )
        )


def test_sync_activities_saves_summary_and_detail() -> None:
    athlete_id = uuid4()

    client = FakeClient()
    activity_repository = (
        FakeActivityRepository()
    )
    detail_repository = (
        FakeActivityDetailRepository()
    )

    service = IntervalsSyncService(
        client=client,
        repository=activity_repository,
        activity_detail_repository=(
            detail_repository
        ),
    )

    synced = service.sync_activities(
        athlete_id,
        date(2026, 8, 28),
        date(2026, 8, 28),
    )

    assert synced == 1

    assert len(
        activity_repository.saved
    ) == 1

    assert len(
        detail_repository.saved
    ) == 1

    detail = (
        detail_repository.saved[0][1]
    )

    assert isinstance(
        detail,
        ActivityDetail,
    )

    assert (
        detail.provider_activity_id
        == "i123"
    )

    assert detail.provider_lap_count == 2
    assert len(detail.intervals) == 1

    assert (
        detail.streams.available_types
        == (
            "time",
            "distance",
            "heartrate",
        )
    )


def test_sync_requests_only_available_coach_streams() -> None:
    client = FakeClient()

    service = IntervalsSyncService(
        client=client,
        repository=FakeActivityRepository(),
        activity_detail_repository=(
            FakeActivityDetailRepository()
        ),
    )

    service.sync_activities(
        uuid4(),
        date(2026, 8, 28),
        date(2026, 8, 28),
    )

    stream_call = next(
        call
        for call in client.calls
        if call[0] == "streams"
    )

    assert (
        stream_call[2]
        == COACH_STREAM_TYPES
    )

    assert "latlng" not in stream_call[2]
    assert "altitude" not in stream_call[2]


def test_sync_excludes_unavailable_optional_streams() -> None:
    client = FakeClient()

    original = client.get_activity_details

    def get_activity_details(
        activity_id,
        *,
        include_intervals=True,
    ):
        result = original(
            activity_id,
            include_intervals=include_intervals,
        )

        result["stream_types"] = [
            "time",
            "distance",
            "heartrate",
            "latlng",
        ]

        return result

    client.get_activity_details = get_activity_details

    service = IntervalsSyncService(
        client=client,
        repository=FakeActivityRepository(),
        activity_detail_repository=(
            FakeActivityDetailRepository()
        ),
    )

    service.sync_activities(
        uuid4(),
        date(2026, 8, 28),
        date(2026, 8, 28),
    )

    stream_call = next(
        call
        for call in client.calls
        if call[0] == "streams"
    )

    assert stream_call[2] == (
        "time",
        "distance",
        "heartrate",
    )


def test_sync_skips_stream_request_when_none_are_useful() -> None:
    client = FakeClient()

    original = client.get_activity_details

    def get_activity_details(
        activity_id,
        *,
        include_intervals=True,
    ):
        result = original(
            activity_id,
            include_intervals=include_intervals,
        )

        result["stream_types"] = [
            "latlng",
            "altitude",
            "temp",
        ]

        return result

    client.get_activity_details = get_activity_details

    detail_repository = FakeActivityDetailRepository()

    service = IntervalsSyncService(
        client=client,
        repository=FakeActivityRepository(),
        activity_detail_repository=detail_repository,
    )

    service.sync_activities(
        uuid4(),
        date(2026, 8, 28),
        date(2026, 8, 28),
    )

    assert not any(
        call[0] == "streams"
        for call in client.calls
    )

    detail = detail_repository.saved[0][1]

    assert detail.streams.available_types == ()


def test_sync_fetches_detail_after_activity_summary() -> None:
    client = FakeClient()

    service = IntervalsSyncService(
        client=client,
        repository=FakeActivityRepository(),
        activity_detail_repository=(
            FakeActivityDetailRepository()
        ),
    )

    service.sync_activities(
        uuid4(),
        date(2026, 8, 28),
        date(2026, 8, 28),
    )

    names = [
        call[0]
        for call in client.calls
    ]

    assert names == [
        "activities",
        "details",
        "streams",
    ]


def test_sync_requires_activity_detail_repository() -> None:
    with pytest.raises(
        TypeError,
        match="activity_detail_repository",
    ):
        IntervalsSyncService(
            client=FakeClient(),
            repository=FakeActivityRepository(),
        )
