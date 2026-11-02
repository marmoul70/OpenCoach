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



def run_coros_sync_job(*, job_id: UUID, athlete_profile_id: UUID) -> None:
    """Exécute l'import COROS dans une session DB dédiée."""
    import json
    import logging
    import os
    from datetime import datetime, timezone
    from sqlalchemy import select
    from opencoach.database.models import IntegrationConnection
    from opencoach.database.session import SessionLocal
    from opencoach.integrations.coros.client import CorosMcpClient
    from opencoach.integrations.coros.oauth import CorosOAuthClientService
    from opencoach.integrations.coros.tokens import refresh_secret_if_needed
    from opencoach.integrations.coros.sync import CorosImportService
    from opencoach.security import SecretCipher

    logger = logging.getLogger(__name__)
    COROS_SYNC_JOBS.running(job_id)
    db = SessionLocal()
    try:
        connection = db.scalar(select(IntegrationConnection).where(
            IntegrationConnection.athlete_profile_id == athlete_profile_id,
            IntegrationConnection.provider == "coros",
        ))
        if connection is None or not connection.enabled or connection.encrypted_secret is None:
            raise RuntimeError("La connexion COROS est absente ou désactivée.")
        cipher = SecretCipher.from_env()
        secret = json.loads(cipher.decrypt(connection.encrypted_secret))
        if secret.get("status") != "connected":
            raise RuntimeError("La connexion COROS doit être réautorisée.")
        oauth = CorosOAuthClientService(redirect_uri=os.getenv("OPENCOACH_COROS_REDIRECT_URI", "http://127.0.0.1:43123/callback"))
        refreshed = refresh_secret_if_needed(secret, oauth, now=datetime.now(timezone.utc).timestamp())
        result = CorosImportService(CorosMcpClient(refreshed["access_token"]), db, athlete_profile_id).import_history(
            (connection.config or {}).get("categories", {}), months=6,
        )
        if refreshed != secret:
            connection.encrypted_secret = cipher.encrypt(json.dumps(refreshed, separators=(",", ":")))
        connection.last_synced_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.commit()
        COROS_SYNC_JOBS.success(job_id, result)
    except Exception:
        db.rollback()
        logger.exception("Échec de la synchronisation COROS (job=%s, profile=%s)", job_id, athlete_profile_id)
        # Ne jamais exposer à l'interface les détails internes, URL, jetons
        # ou réponses brutes renvoyés par le fournisseur.
        COROS_SYNC_JOBS.failure(job_id, "La synchronisation COROS a échoué. Vérifie la connexion puis consulte les journaux OpenCoach.")
    finally:
        db.close()
