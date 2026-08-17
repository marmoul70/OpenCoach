from datetime import date, timedelta
from uuid import uuid4

import pytest

from opencoach.services import (
    DEFAULT_SYNC_DAYS,
    IntervalsApplicationService,
)


class FakeIntervalsSyncService:
    def __init__(
        self,
        result: int = 0,
    ) -> None:
        self.result = result
        self.calls = []

    def sync_activities(
        self,
        athlete_profile_id,
        oldest: date,
        newest: date,
    ) -> int:
        self.calls.append(
            (
                athlete_profile_id,
                oldest,
                newest,
            )
        )

        return self.result


def test_sync_activities_uses_requested_period() -> None:
    sync_service = FakeIntervalsSyncService(
        result=21,
    )

    service = IntervalsApplicationService(
        sync_service,
    )

    profile_id = uuid4()

    result = service.sync_activities(
        profile_id,
        newest=date(2026, 8, 17),
        days=30,
    )

    assert result == 21

    assert sync_service.calls == [
        (
            profile_id,
            date(2026, 7, 18),
            date(2026, 8, 17),
        )
    ]


def test_sync_activities_uses_default_period() -> None:
    sync_service = FakeIntervalsSyncService()

    service = IntervalsApplicationService(
        sync_service,
    )

    profile_id = uuid4()

    service.sync_activities(
        profile_id,
        newest=date(2026, 8, 17),
    )

    assert sync_service.calls == [
        (
            profile_id,
            date(2026, 8, 17)
            - timedelta(days=DEFAULT_SYNC_DAYS),
            date(2026, 8, 17),
        )
    ]


@pytest.mark.parametrize(
    "days",
    [
        0,
        -1,
        -30,
    ],
)
def test_sync_activities_rejects_invalid_period(
    days: int,
) -> None:
    sync_service = FakeIntervalsSyncService()

    service = IntervalsApplicationService(
        sync_service,
    )

    with pytest.raises(
        ValueError,
        match="période de synchronisation",
    ):
        service.sync_activities(
            uuid4(),
            newest=date(2026, 8, 17),
            days=days,
        )

    assert sync_service.calls == []