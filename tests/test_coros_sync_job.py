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
