from uuid import uuid4

from opencoach.services.intervals_initial_sync_job import (
    IntervalsInitialSyncJobStore,
)


def test_job_creation_is_pending():
    store = IntervalsInitialSyncJobStore()
    athlete_id = uuid4()

    job = store.create(
        athlete_id,
    )

    assert job.status == "pending"
    assert (
        job.athlete_profile_id
        == athlete_id
    )

    assert store.get(
        job.id,
    ) is job


def test_find_active_job():
    store = IntervalsInitialSyncJobStore()
    athlete_id = uuid4()

    job = store.create(
        athlete_id,
    )

    assert (
        store.find_active(
            athlete_id,
        )
        is job
    )

    store.mark_running(
        job.id,
    )

    assert (
        store.find_active(
            athlete_id,
        )
        is job
    )


def test_success_finishes_job():
    store = IntervalsInitialSyncJobStore()
    athlete_id = uuid4()

    job = store.create(
        athlete_id,
    )

    store.mark_running(
        job.id,
    )

    store.mark_success(
        job.id,
        synced_activities=42,
        synced_wellness_days=88,
        days=90,
    )

    result = store.get(
        job.id,
    )

    assert result is not None
    assert result.status == "success"
    assert result.synced_activities == 42
    assert result.synced_wellness_days == 88
    assert result.days == 90
    assert result.finished_at is not None

    assert (
        store.find_active(
            athlete_id,
        )
        is None
    )


def test_error_finishes_job():
    store = IntervalsInitialSyncJobStore()

    job = store.create(
        uuid4(),
    )

    store.mark_running(
        job.id,
    )

    store.mark_error(
        job.id,
        "Intervals indisponible",
    )

    result = store.get(
        job.id,
    )

    assert result is not None
    assert result.status == "error"
    assert (
        result.error
        == "Intervals indisponible"
    )

    assert result.finished_at is not None
