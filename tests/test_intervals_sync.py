from datetime import date

from opencoach.integrations.intervals import (
    IntervalsSyncService,
)
from opencoach.models import (
    Activity,
    ActivityDetail,
)


class FakeIntervalsClient:
    def __init__(
        self,
        activities: list[dict],
    ) -> None:
        self.activities = activities
        self.calls = []

    def get_activities(
        self,
        oldest: date,
        newest: date,
    ) -> list[dict]:
        self.calls.append(
            (
                "activities",
                oldest,
                newest,
            ),
        )

        return self.activities

    def get_activity_details(
        self,
        activity_id: str,
        *,
        include_intervals: bool = True,
    ) -> dict:
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
            "icu_lap_count": 1,
            "interval_summary": [],
            "icu_intervals": [
                {
                    "id": 1,
                    "type": "WORK",
                    "label": None,
                    "start_index": 0,
                    "end_index": 60,
                    "start_time": 0,
                    "end_time": 60,
                    "distance": 200.0,
                    "moving_time": 60,
                    "elapsed_time": 60,
                    "average_speed": 3.33,
                    "average_heartrate": 140,
                    "max_heartrate": 150,
                    "average_cadence": 90.0,
                    "total_elevation_gain": 0.0,
                    "training_load": None,
                },
            ],
        }

    def get_activity_streams(
        self,
        activity_id: str,
        *,
        types: tuple[str, ...],
    ) -> list[dict]:
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
                "data": [
                    0,
                    1,
                    2,
                ],
            },
            {
                "type": "distance",
                "data": [
                    0.0,
                    3.3,
                    6.6,
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
        ]


class FakeActivityRepository:
    def __init__(self) -> None:
        self.saved = []

    def save_activity(
        self,
        athlete_profile_id,
        activity: Activity,
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
        detail: ActivityDetail,
    ) -> None:
        self.saved.append(
            (
                athlete_profile_id,
                detail,
            )
        )


class FakeWellnessRepository:
    def __init__(self) -> None:
        self.saved = []

    def save_wellness_day(
        self,
        athlete_profile_id,
        wellness,
    ) -> None:
        self.saved.append(
            (
                athlete_profile_id,
                wellness,
            )
        )


def create_activity_data(
    activity_id: str,
) -> dict:
    return {
        "id": activity_id,
        "name": "Morning Course à pied",
        "type": "Run",
        "source": "SUUNTO",
        "start_date": "2026-08-14T06:01:34Z",
    }


def create_service(
    client: FakeIntervalsClient,
    repository: FakeActivityRepository,
    *,
    detail_repository: (
        FakeActivityDetailRepository | None
    ) = None,
    wellness_repository: (
        FakeWellnessRepository | None
    ) = None,
) -> IntervalsSyncService:
    return IntervalsSyncService(
        client=client,
        repository=repository,
        activity_detail_repository=(
            detail_repository
            or FakeActivityDetailRepository()
        ),
        wellness_repository=wellness_repository,
    )


def test_sync_activities_imports_all_activities() -> None:
    client = FakeIntervalsClient(
        [
            create_activity_data("i1"),
            create_activity_data("i2"),
        ]
    )

    repository = FakeActivityRepository()
    detail_repository = (
        FakeActivityDetailRepository()
    )

    service = create_service(
        client,
        repository,
        detail_repository=detail_repository,
    )

    count = service.sync_activities(
        athlete_profile_id="profile-1",
        oldest=date(2026, 8, 1),
        newest=date(2026, 8, 17),
    )

    assert count == 2
    assert len(repository.saved) == 2
    assert len(detail_repository.saved) == 2

    assert (
        repository.saved[0][0]
        == "profile-1"
    )

    assert (
        repository.saved[0][1].provider
        == "intervals"
    )

    assert (
        repository.saved[0][1]
        .provider_activity_id
        == "i1"
    )

    assert (
        repository.saved[1][1]
        .provider_activity_id
        == "i2"
    )

    assert (
        detail_repository.saved[0][1]
        .provider_activity_id
        == "i1"
    )

    assert (
        detail_repository.saved[1][1]
        .provider_activity_id
        == "i2"
    )


def test_sync_activities_forwards_date_range() -> None:
    client = FakeIntervalsClient([])

    repository = FakeActivityRepository()

    service = create_service(
        client,
        repository,
    )

    oldest = date(2026, 8, 1)
    newest = date(2026, 8, 17)

    service.sync_activities(
        athlete_profile_id="profile-1",
        oldest=oldest,
        newest=newest,
    )

    assert client.calls == [
        (
            "activities",
            oldest,
            newest,
        )
    ]


def test_sync_activities_returns_zero_when_empty() -> None:
    client = FakeIntervalsClient([])

    repository = FakeActivityRepository()
    detail_repository = (
        FakeActivityDetailRepository()
    )

    service = create_service(
        client,
        repository,
        detail_repository=detail_repository,
    )

    count = service.sync_activities(
        athlete_profile_id="profile-1",
        oldest=date(2026, 8, 1),
        newest=date(2026, 8, 17),
    )

    assert count == 0
    assert repository.saved == []
    assert detail_repository.saved == []


def test_sync_activities_fetches_details_and_streams() -> None:
    client = FakeIntervalsClient(
        [
            create_activity_data("i1"),
        ]
    )

    service = create_service(
        client,
        FakeActivityRepository(),
    )

    service.sync_activities(
        athlete_profile_id="profile-1",
        oldest=date(2026, 8, 1),
        newest=date(2026, 8, 17),
    )

    assert client.calls[0][0] == "activities"

    assert client.calls[1] == (
        "details",
        "i1",
        True,
    )

    assert client.calls[2][0] == "streams"
    assert client.calls[2][1] == "i1"

    stream_types = client.calls[2][2]

    assert "time" in stream_types
    assert "distance" in stream_types
    assert "heartrate" in stream_types
    assert "latlng" not in stream_types


def test_sync_wellness_imports_all_days() -> None:
    client = FakeIntervalsClient([])

    client.get_wellness = lambda oldest, newest: [
        {
            "id": "2026-08-17",
            "ctl": 16.0,
            "atl": 7.0,
            "rampRate": -1.5,
            "steps": 5000,
        },
        {
            "id": "2026-08-18",
            "ctl": 17.0,
            "atl": 8.0,
            "rampRate": -1.0,
            "steps": 6000,
        },
    ]

    activity_repository = (
        FakeActivityRepository()
    )

    wellness_repository = (
        FakeWellnessRepository()
    )

    service = create_service(
        client,
        activity_repository,
        wellness_repository=wellness_repository,
    )

    count = service.sync_wellness(
        athlete_profile_id="profile-1",
        oldest=date(2026, 8, 17),
        newest=date(2026, 8, 18),
    )

    assert count == 2

    assert len(
        wellness_repository.saved
    ) == 2

    assert (
        wellness_repository.saved[0][1].date
        == date(
            2026,
            8,
            17,
        )
    )

    assert (
        wellness_repository.saved[1][1].steps
        == 6000
    )


def test_sync_wellness_requires_repository() -> None:
    client = FakeIntervalsClient([])

    service = create_service(
        client,
        FakeActivityRepository(),
    )

    try:
        service.sync_wellness(
            athlete_profile_id="profile-1",
            oldest=date(2026, 8, 17),
            newest=date(2026, 8, 18),
        )

    except RuntimeError as exc:
        assert (
            "repository Wellness"
            in str(exc)
        )

    else:
        raise AssertionError(
            "RuntimeError attendu."
        )
