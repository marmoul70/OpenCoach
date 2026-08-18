from datetime import date

from opencoach.integrations.intervals import (
    IntervalsSyncService,
)
from opencoach.models import Activity


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
            (oldest, newest),
        )

        return self.activities


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


def test_sync_activities_imports_all_activities() -> None:
    client = FakeIntervalsClient(
        [
            create_activity_data("i1"),
            create_activity_data("i2"),
        ]
    )

    repository = FakeActivityRepository()

    service = IntervalsSyncService(
        client=client,
        repository=repository,
    )

    count = service.sync_activities(
        athlete_profile_id="profile-1",
        oldest=date(2026, 8, 1),
        newest=date(2026, 8, 17),
    )

    assert count == 2
    assert len(repository.saved) == 2

    assert repository.saved[0][0] == "profile-1"
    assert repository.saved[0][1].provider == "intervals"
    assert repository.saved[0][1].provider_activity_id == "i1"

    assert repository.saved[1][1].provider_activity_id == "i2"


def test_sync_activities_forwards_date_range() -> None:
    client = FakeIntervalsClient([])

    repository = FakeActivityRepository()

    service = IntervalsSyncService(
        client=client,
        repository=repository,
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
            oldest,
            newest,
        )
    ]


def test_sync_activities_returns_zero_when_empty() -> None:
    client = FakeIntervalsClient([])

    repository = FakeActivityRepository()

    service = IntervalsSyncService(
        client=client,
        repository=repository,
    )

    count = service.sync_activities(
        athlete_profile_id="profile-1",
        oldest=date(2026, 8, 1),
        newest=date(2026, 8, 17),
    )

    assert count == 0
    assert repository.saved == []

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

    activity_repository = FakeActivityRepository()
    wellness_repository = FakeWellnessRepository()

    service = IntervalsSyncService(
        client=client,
        repository=activity_repository,
        wellness_repository=wellness_repository,
    )

    count = service.sync_wellness(
        athlete_profile_id="profile-1",
        oldest=date(2026, 8, 17),
        newest=date(2026, 8, 18),
    )

    assert count == 2
    assert len(wellness_repository.saved) == 2
    assert wellness_repository.saved[0][1].date == date(
        2026,
        8,
        17,
    )
    assert wellness_repository.saved[1][1].steps == 6000


def test_sync_wellness_requires_repository() -> None:
    client = FakeIntervalsClient([])

    service = IntervalsSyncService(
        client=client,
        repository=FakeActivityRepository(),
    )

    try:
        service.sync_wellness(
            athlete_profile_id="profile-1",
            oldest=date(2026, 8, 17),
            newest=date(2026, 8, 18),
        )
    except RuntimeError as exc:
        assert "repository Wellness" in str(exc)
    else:
        raise AssertionError(
            "RuntimeError attendu."
        )