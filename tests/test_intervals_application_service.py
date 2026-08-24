from datetime import (
    date,
    datetime,
    timedelta,
    timezone,
)
from uuid import uuid4

import pytest

from opencoach.services import (
    DEFAULT_SYNC_DAYS,
    IntervalsApplicationService,
    IntervalsSyncResult,
)


class FakeIntegrationConnectionService:
    def __init__(self) -> None:
        self.calls = []

    def mark_synced(
        self,
        athlete_profile_id,
        provider: str,
        synced_at: datetime,
    ) -> None:
        self.calls.append(
            (
                athlete_profile_id,
                provider,
                synced_at,
            )
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
                "activities",
                athlete_profile_id,
                oldest,
                newest,
            )
        )

        return self.result

    def sync_wellness(
        self,
        athlete_profile_id,
        oldest: date,
        newest: date,
    ) -> int:
        self.calls.append(
            (
                "wellness",
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
            "activities",
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
            "activities",
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

def test_sync_all_synchronizes_and_marks_connection() -> None:
    sync_service = FakeIntervalsSyncService(
        result=21,
    )

    connection_service = (
        FakeIntegrationConnectionService()
    )

    synced_at = datetime(
        2026,
        8,
        24,
        15,
        0,
        tzinfo=timezone.utc,
    )

    service = IntervalsApplicationService(
        sync_service=sync_service,
        connection_service=connection_service,
        clock=lambda: synced_at,
    )

    profile_id = uuid4()

    result = service.sync_all(
        profile_id,
        newest=date(2026, 8, 18),
        days=30,
    )

    assert result == IntervalsSyncResult(
        synced_activities=21,
        synced_wellness_days=21,
        oldest=date(2026, 7, 19),
        newest=date(2026, 8, 18),
        synced_at=synced_at,
    )

    assert sync_service.calls == [
        (
            "activities",
            profile_id,
            date(2026, 7, 19),
            date(2026, 8, 18),
        ),
        (
            "wellness",
            profile_id,
            date(2026, 7, 19),
            date(2026, 8, 18),
        ),
    ]

    assert connection_service.calls == [
        (
            profile_id,
            "intervals",
            synced_at,
        )
    ]


def test_sync_all_does_not_mark_connection_when_sync_fails() -> None:
    class FailingSyncService(
        FakeIntervalsSyncService
    ):
        def sync_wellness(
            self,
            athlete_profile_id,
            oldest: date,
            newest: date,
        ) -> int:
            raise RuntimeError(
                "wellness indisponible"
            )

    sync_service = FailingSyncService()

    connection_service = (
        FakeIntegrationConnectionService()
    )

    service = IntervalsApplicationService(
        sync_service=sync_service,
        connection_service=connection_service,
    )

    with pytest.raises(
        RuntimeError,
        match="wellness indisponible",
    ):
        service.sync_all(
            uuid4(),
            newest=date(2026, 8, 18),
            days=30,
        )

    assert connection_service.calls == []


def test_incremental_sync_uses_last_sync_with_lookback() -> None:
    """Une synchro incrémentale relit une petite fenêtre de sécurité."""

    class FakeConnection:
        last_synced_at = datetime(
            2026,
            8,
            20,
            14,
            0,
            tzinfo=timezone.utc,
        )

    class FakeConnectionService(
        FakeIntegrationConnectionService
    ):
        def get_connection(
            self,
            athlete_profile_id,
            provider: str,
        ):
            return FakeConnection()

    sync_service = FakeIntervalsSyncService(
        result=3,
    )

    connection_service = FakeConnectionService()

    service = IntervalsApplicationService(
        sync_service=sync_service,
        connection_service=connection_service,
    )

    profile_id = uuid4()

    result = service.sync_incremental(
        profile_id,
        newest=date(2026, 8, 24),
    )

    assert result.oldest == date(2026, 8, 18)
    assert result.newest == date(2026, 8, 24)

    assert sync_service.calls == [
        (
            "activities",
            profile_id,
            date(2026, 8, 18),
            date(2026, 8, 24),
        ),
        (
            "wellness",
            profile_id,
            date(2026, 8, 18),
            date(2026, 8, 24),
        ),
    ]


def test_incremental_sync_uses_default_window_without_previous_sync() -> None:
    """Sans synchro précédente, on utilise la fenêtre initiale."""

    class FakeConnection:
        last_synced_at = None

    class FakeConnectionService(
        FakeIntegrationConnectionService
    ):
        def get_connection(
            self,
            athlete_profile_id,
            provider: str,
        ):
            return FakeConnection()

    sync_service = FakeIntervalsSyncService()

    connection_service = FakeConnectionService()

    service = IntervalsApplicationService(
        sync_service=sync_service,
        connection_service=connection_service,
    )

    result = service.sync_incremental(
        uuid4(),
        newest=date(2026, 8, 24),
    )

    assert result.oldest == (
        date(2026, 8, 24)
        - timedelta(days=DEFAULT_SYNC_DAYS)
    )


def test_incremental_sync_requires_connection_service() -> None:
    """Une synchro incrémentale nécessite l'état de connexion."""

    service = IntervalsApplicationService(
        sync_service=FakeIntervalsSyncService(),
    )

    with pytest.raises(
        RuntimeError,
        match="connection_service",
    ):
        service.sync_incremental(
            uuid4(),
            newest=date(2026, 8, 24),
        )


@pytest.mark.parametrize(
    "initial_days",
    [
        0,
        -1,
    ],
)
def test_incremental_sync_rejects_invalid_initial_days(
    initial_days: int,
) -> None:
    class FakeConnection:
        last_synced_at = None

    class FakeConnectionService(
        FakeIntegrationConnectionService
    ):
        def get_connection(
            self,
            athlete_profile_id,
            provider: str,
        ):
            return FakeConnection()

    service = IntervalsApplicationService(
        sync_service=FakeIntervalsSyncService(),
        connection_service=FakeConnectionService(),
    )

    with pytest.raises(
        ValueError,
        match="initial_days",
    ):
        service.sync_incremental(
            uuid4(),
            newest=date(2026, 8, 24),
            initial_days=initial_days,
        )


def test_incremental_sync_rejects_negative_lookback() -> None:
    class FakeConnection:
        last_synced_at = datetime(
            2026,
            8,
            20,
            tzinfo=timezone.utc,
        )

    class FakeConnectionService(
        FakeIntegrationConnectionService
    ):
        def get_connection(
            self,
            athlete_profile_id,
            provider: str,
        ):
            return FakeConnection()

    service = IntervalsApplicationService(
        sync_service=FakeIntervalsSyncService(),
        connection_service=FakeConnectionService(),
    )

    with pytest.raises(
        ValueError,
        match="lookback_days",
    ):
        service.sync_incremental(
            uuid4(),
            newest=date(2026, 8, 24),
            lookback_days=-1,
        )
