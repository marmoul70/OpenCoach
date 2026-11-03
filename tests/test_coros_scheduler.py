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



def test_scheduler_does_not_evict_stale_lock_owned_by_live_worker(monkeypatch):
    from types import SimpleNamespace
    from uuid import uuid4

    from opencoach.commands import sync_coros

    now = datetime(2026, 11, 3, 12, 0)
    profile_id = uuid4()
    previous_job_id = str(uuid4())
    lock = SimpleNamespace(
        athlete_profile_id=profile_id,
        job_id=previous_job_id,
        acquired_at=now - timedelta(minutes=31),
    )
    connection = SimpleNamespace(config={
        "coros_sync_job": {
            "job_id": previous_job_id,
            "status": "running",
            "worker_pid": 12345,
        },
    })

    class FakeSession:
        deleted = []
        added = []
        commits = 0

        def get(self, _model, _key):
            return lock

        def scalar(self, _statement):
            return connection

        def delete(self, value):
            self.deleted.append(value)

        def add(self, value):
            self.added.append(value)

        def commit(self):
            self.commits += 1

    monkeypatch.setattr(sync_coros.os, "kill", lambda _pid, _signal: None)
    session = FakeSession()

    acquired = sync_coros._acquire_lock(
        session,
        profile_id=profile_id,
        job_id=uuid4(),
        now=now,
    )

    assert acquired is False
    assert session.deleted == []
    assert session.added == []
    assert session.commits == 0


def test_scheduler_reclaims_stale_lock_when_worker_process_is_gone(monkeypatch):
    from types import SimpleNamespace
    from uuid import uuid4

    from opencoach.commands import sync_coros

    now = datetime(2026, 11, 3, 12, 0)
    profile_id = uuid4()
    previous_job_id = str(uuid4())
    lock = SimpleNamespace(
        athlete_profile_id=profile_id,
        job_id=previous_job_id,
        acquired_at=now - timedelta(minutes=31),
    )
    connection = SimpleNamespace(config={
        "coros_sync_job": {
            "job_id": previous_job_id,
            "status": "running",
            "worker_pid": 12345,
        },
    })

    class FakeSession:
        deleted = []
        added = []
        commits = 0

        def get(self, _model, _key):
            return lock

        def scalar(self, _statement):
            return connection

        def delete(self, value):
            self.deleted.append(value)

        def add(self, value):
            self.added.append(value)

        def commit(self):
            self.commits += 1

    def missing_process(_pid, _signal):
        raise ProcessLookupError()

    monkeypatch.setattr(sync_coros.os, "kill", missing_process)
    session = FakeSession()

    acquired = sync_coros._acquire_lock(
        session,
        profile_id=profile_id,
        job_id=uuid4(),
        now=now,
    )

    assert acquired is True
    assert session.deleted == [lock]
    assert len(session.added) == 1
    assert session.commits == 2


def test_scheduler_keeps_stale_lock_when_process_check_is_inconclusive(monkeypatch):
    from types import SimpleNamespace
    from uuid import uuid4

    from opencoach.commands import sync_coros

    now = datetime(2026, 11, 3, 12, 0)
    profile_id = uuid4()
    previous_job_id = str(uuid4())
    lock = SimpleNamespace(
        athlete_profile_id=profile_id,
        job_id=previous_job_id,
        acquired_at=now - timedelta(minutes=31),
    )
    connection = SimpleNamespace(config={
        "coros_sync_job": {
            "job_id": previous_job_id,
            "status": "running",
            "worker_pid": 12345,
        },
    })

    class FakeSession:
        deleted = []
        added = []
        commits = 0

        def get(self, _model, _key):
            return lock

        def scalar(self, _statement):
            return connection

        def delete(self, value):
            self.deleted.append(value)

        def add(self, value):
            self.added.append(value)

        def commit(self):
            self.commits += 1

    def inaccessible_process(_pid, _signal):
        raise PermissionError()

    monkeypatch.setattr(sync_coros.os, "kill", inaccessible_process)
    session = FakeSession()

    acquired = sync_coros._acquire_lock(
        session,
        profile_id=profile_id,
        job_id=uuid4(),
        now=now,
    )

    assert acquired is False
    assert session.deleted == []
    assert session.added == []
    assert session.commits == 0
