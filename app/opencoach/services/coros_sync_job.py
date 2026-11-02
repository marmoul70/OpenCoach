from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from uuid import UUID, uuid4
from typing import Any


@dataclass(slots=True)
class CorosSyncJob:
    id: UUID
    athlete_profile_id: UUID
    status: str = "pending"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: datetime | None = None
    result: dict[str, Any] | None = None
    error: str | None = None


class CorosSyncJobStore:
    def __init__(self) -> None:
        self._jobs: dict[UUID, CorosSyncJob] = {}
        self._lock = Lock()

    def create(self, profile_id: UUID) -> CorosSyncJob:
        job = CorosSyncJob(id=uuid4(), athlete_profile_id=profile_id)
        with self._lock:
            self._jobs[job.id] = job
        return job

    def find_active(self, profile_id: UUID) -> CorosSyncJob | None:
        with self._lock:
            return next((job for job in self._jobs.values() if job.athlete_profile_id == profile_id and job.status in {"pending", "running"}), None)

    def get(self, job_id: UUID) -> CorosSyncJob | None:
        with self._lock:
            return self._jobs.get(job_id)

    def running(self, job_id: UUID) -> None:
        with self._lock:
            self._jobs[job_id].status = "running"

    def success(self, job_id: UUID, result: dict[str, Any]) -> None:
        with self._lock:
            job = self._jobs[job_id]
            job.status = "success"
            job.result = result
            job.finished_at = datetime.now(timezone.utc)

    def failure(self, job_id: UUID, error: str) -> None:
        with self._lock:
            job = self._jobs[job_id]
            job.status = "error"
            job.error = error
            job.finished_at = datetime.now(timezone.utc)


COROS_SYNC_JOBS = CorosSyncJobStore()
