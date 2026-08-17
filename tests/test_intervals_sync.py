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