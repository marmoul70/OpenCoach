from datetime import datetime, timedelta, timezone

from opencoach.commands.sync_coros import is_sync_due


def test_coros_sync_disabled_when_interval_is_zero():
    assert not is_sync_due(
        now=datetime(2026, 11, 2, 12, 0),
        interval_hours=0,
        last_synced_at=None,
    )


def test_coros_sync_due_immediately_when_never_synced():
    assert is_sync_due(
        now=datetime(2026, 11, 2, 12, 0),
        interval_hours=12,
        last_synced_at=None,
    )


def test_coros_sync_due_only_after_configured_interval():
    now = datetime(2026, 11, 2, 12, 0, tzinfo=timezone.utc)
    last_sync = now - timedelta(hours=11, minutes=59)
    assert not is_sync_due(
        now=now,
        interval_hours=12,
        last_synced_at=last_sync,
    )
    assert is_sync_due(
        now=now,
        interval_hours=12,
        last_synced_at=now - timedelta(hours=12),
    )
