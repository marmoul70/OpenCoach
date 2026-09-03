from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock
from uuid import UUID, uuid4

from opencoach.database.repositories import (
    SqlActivityDetailRepository,
    SqlActivityRepository,
    SqlIntegrationConnectionRepository,
    SqlWellnessRepository,
)
from opencoach.database.session import SessionLocal
from opencoach.integrations.intervals import (
    IntervalsClient,
    IntervalsSyncService,
)
from opencoach.security import SecretCipher
from opencoach.services.integration_connection import (
    IntegrationConnectionService,
)
from opencoach.services.intervals_sync import (
    IntervalsApplicationService,
)


@dataclass(slots=True)
class InitialSyncJob:
    id: UUID
    athlete_profile_id: UUID
    status: str
    created_at: datetime
    finished_at: datetime | None = None

    synced_activities: int = 0
    synced_wellness_days: int = 0
    days: int = 90

    error: str | None = None


class IntervalsInitialSyncJobStore:
    """Stockage mémoire des jobs de bootstrap Intervals.icu."""

    def __init__(self) -> None:
        self._jobs: dict[UUID, InitialSyncJob] = {}
        self._lock = Lock()

    def create(
        self,
        athlete_profile_id: UUID,
    ) -> InitialSyncJob:
        job = InitialSyncJob(
            id=uuid4(),
            athlete_profile_id=athlete_profile_id,
            status="pending",
            created_at=datetime.now(
                timezone.utc,
            ),
        )

        with self._lock:
            self._jobs[job.id] = job

        return job

    def find_active(
        self,
        athlete_profile_id: UUID,
    ) -> InitialSyncJob | None:
        with self._lock:
            for job in self._jobs.values():
                if (
                    job.athlete_profile_id
                    == athlete_profile_id
                    and job.status
                    in {
                        "pending",
                        "running",
                    }
                ):
                    return job

        return None


    def get(
        self,
        job_id: UUID,
    ) -> InitialSyncJob | None:
        with self._lock:
            return self._jobs.get(job_id)

    def mark_running(
        self,
        job_id: UUID,
    ) -> None:
        with self._lock:
            job = self._jobs[job_id]
            job.status = "running"

    def mark_success(
        self,
        job_id: UUID,
        *,
        synced_activities: int,
        synced_wellness_days: int,
        days: int,
    ) -> None:
        with self._lock:
            job = self._jobs[job_id]

            job.status = "success"
            job.synced_activities = (
                synced_activities
            )
            job.synced_wellness_days = (
                synced_wellness_days
            )
            job.days = days

            job.finished_at = datetime.now(
                timezone.utc,
            )

    def mark_error(
        self,
        job_id: UUID,
        error: str,
    ) -> None:
        with self._lock:
            job = self._jobs[job_id]

            job.status = "error"
            job.error = error

            job.finished_at = datetime.now(
                timezone.utc,
            )


INITIAL_SYNC_JOBS = (
    IntervalsInitialSyncJobStore()
)


def run_initial_sync_job(
    *,
    job_id: UUID,
    athlete_profile_id: UUID,
) -> None:
    """Exécute le bootstrap avec sa propre session DB."""

    INITIAL_SYNC_JOBS.mark_running(
        job_id,
    )

    db = SessionLocal()

    try:
        connection_repository = (
            SqlIntegrationConnectionRepository(
                db,
            )
        )

        connection_service = (
            IntegrationConnectionService(
                repository=(
                    connection_repository
                ),
                cipher=(
                    SecretCipher.from_env()
                ),
            )
        )

        credentials = (
            connection_service.get_credentials(
                athlete_profile_id,
                "intervals",
            )
        )

        client = IntervalsClient(
            api_key=credentials.secret,
            athlete_id=(
                credentials.athlete_id
            ),
        )

        sync_service = IntervalsSyncService(
            client=client,
            repository=(
                SqlActivityRepository(
                    db,
                )
            ),
            wellness_repository=(
                SqlWellnessRepository(
                    db,
                )
            ),
            activity_detail_repository=(
                SqlActivityDetailRepository(
                    db,
                )
            ),
        )

        service = IntervalsApplicationService(
            sync_service=sync_service,
            connection_service=(
                connection_service
            ),
        )

        result = service.sync_initial_history(
            athlete_profile_id,
        )

        INITIAL_SYNC_JOBS.mark_success(
            job_id,
            synced_activities=(
                result.synced_activities
            ),
            synced_wellness_days=(
                result.synced_wellness_days
            ),
            days=90,
        )

    except Exception as exc:
        db.rollback()

        INITIAL_SYNC_JOBS.mark_error(
            job_id,
            str(exc),
        )

    finally:
        db.close()

