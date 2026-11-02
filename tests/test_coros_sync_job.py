from uuid import uuid4

from opencoach.services.coros_sync_job import CorosSyncJobStore


def test_coros_sync_job_store_tracks_owner_and_terminal_result():
    store = CorosSyncJobStore()
    profile_id = uuid4()
    job = store.create(profile_id)

    assert job.status == "pending"
    assert store.find_active(profile_id).id == job.id
    store.running(job.id)
    store.success(job.id, {"imported_snapshots": {"sleep": 12}})

    saved = store.get(job.id)
    assert saved.status == "success"
    assert saved.result["imported_snapshots"]["sleep"] == 12
    assert saved.finished_at is not None
    assert store.find_active(profile_id) is None


def test_coros_sync_job_store_ignores_external_scheduled_job_updates():
    store = CorosSyncJobStore()
    unknown_job_id = uuid4()

    store.running(unknown_job_id)
    store.success(unknown_job_id, {"ok": True})
    store.failure(unknown_job_id, "error")

    assert store.get(unknown_job_id) is None


def test_coros_sync_job_store_can_discard_rejected_job():
    store = CorosSyncJobStore()
    job = store.create(uuid4())

    store.discard(job.id)

    assert store.get(job.id) is None
    assert store.find_active(job.athlete_profile_id) is None

def test_incremental_coros_sync_requires_persisted_activities():
    from opencoach.services.coros_sync_job import should_use_incremental_coros_sync

    assert should_use_incremental_coros_sync(
        {"coros_initial_import_completed": True},
        has_coros_activities=True,
    ) is True
    assert should_use_incremental_coros_sync(
        {"coros_initial_import_completed": True},
        has_coros_activities=False,
    ) is False
    assert should_use_incremental_coros_sync(
        {"coros_initial_import_completed": False},
        has_coros_activities=True,
    ) is False
    assert should_use_incremental_coros_sync({}, has_coros_activities=False) is False
