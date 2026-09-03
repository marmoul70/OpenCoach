from datetime import date, datetime, timezone
from uuid import uuid4

import pytest

from opencoach.services.intervals_sync import (
    INITIAL_SYNC_DAYS,
    IntervalsApplicationService,
    IntervalsInitialSyncAlreadyCompletedError,
)


class FakeConnection:
    def __init__(
        self,
        last_synced_at=None,
    ):
        self.last_synced_at = last_synced_at


class FakeConnectionService:
    def __init__(
        self,
        connection,
    ):
        self.connection = connection

    def get_connection(
        self,
        athlete_profile_id,
        provider,
    ):
        assert provider == "intervals"

        return self.connection

    def mark_synced(
        self,
        athlete_profile_id,
        provider,
        synced_at,
    ):
        self.connection.last_synced_at = (
            synced_at
        )


class FakeSyncService:
    def __init__(self):
        self.activity_period = None
        self.wellness_period = None

    def sync_activities(
        self,
        athlete_profile_id,
        oldest,
        newest,
    ):
        self.activity_period = (
            oldest,
            newest,
        )

        return 12

    def sync_wellness(
        self,
        athlete_profile_id,
        oldest,
        newest,
    ):
        self.wellness_period = (
            oldest,
            newest,
        )

        return 75


def test_initial_sync_uses_90_days():
    sync_service = FakeSyncService()

    connection_service = (
        FakeConnectionService(
            FakeConnection(),
        )
    )

    service = IntervalsApplicationService(
        sync_service=sync_service,
        connection_service=(
            connection_service
        ),
        clock=lambda: datetime(
            2026,
            9,
            3,
            tzinfo=timezone.utc,
        ),
    )

    athlete_id = uuid4()

    result = service.sync_initial_history(
        athlete_id,
        newest=date(
            2026,
            9,
            3,
        ),
    )

    assert INITIAL_SYNC_DAYS == 90

    assert result.synced_activities == 12
    assert result.synced_wellness_days == 75

    assert result.newest == date(
        2026,
        9,
        3,
    )

    assert (
        result.newest
        - result.oldest
    ).days == 90

    assert (
        sync_service.activity_period
        == sync_service.wellness_period
    )


def test_initial_sync_marks_connection_synced():
    connection = FakeConnection()

    connection_service = (
        FakeConnectionService(
            connection,
        )
    )

    service = IntervalsApplicationService(
        sync_service=FakeSyncService(),
        connection_service=(
            connection_service
        ),
        clock=lambda: datetime(
            2026,
            9,
            3,
            12,
            30,
            tzinfo=timezone.utc,
        ),
    )

    service.sync_initial_history(
        uuid4(),
    )

    assert (
        connection.last_synced_at
        is not None
    )


def test_initial_sync_cannot_run_twice():
    connection = FakeConnection(
        last_synced_at=datetime(
            2026,
            9,
            1,
            tzinfo=timezone.utc,
        ),
    )

    service = IntervalsApplicationService(
        sync_service=FakeSyncService(),
        connection_service=(
            FakeConnectionService(
                connection,
            )
        ),
    )

    with pytest.raises(
        IntervalsInitialSyncAlreadyCompletedError,
    ):
        service.sync_initial_history(
            uuid4(),
        )
