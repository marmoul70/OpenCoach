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

    def discard(self, job_id: UUID) -> None:
        with self._lock:
            self._jobs.pop(job_id, None)

    def running(self, job_id: UUID) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is not None:
                job.status = "running"

    def success(self, job_id: UUID, result: dict[str, Any]) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return
            job.status = "success"
            job.result = result
            job.finished_at = datetime.now(timezone.utc)

    def failure(self, job_id: UUID, error: str) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return
            job.status = "error"
            job.error = error
            job.finished_at = datetime.now(timezone.utc)


COROS_SYNC_JOBS = CorosSyncJobStore()
def should_use_incremental_coros_sync(config: dict[str, Any], has_coros_activities: bool) -> bool:
    """Only use the seven-day window after activities exist in the canonical table."""
    return bool(config.get("coros_initial_import_completed")) and has_coros_activities


def prepare_coros_checkpoint(
    checkpoint: dict[str, Any] | None,
    *,
    initial_import_completed: bool,
) -> dict[str, Any]:
    """Do not let a stale completed marker skip an unfinished initial activity import."""
    prepared = dict(checkpoint or {})
    if initial_import_completed:
        return prepared

    raw_completed = prepared.get("_completed", "")
    completed = (
        set(filter(None, raw_completed.split(",")))
        if isinstance(raw_completed, str)
        else set()
    )
    completed.discard("activities")
    if completed:
        prepared["_completed"] = ",".join(sorted(completed))
    else:
        prepared.pop("_completed", None)
    return prepared




def run_coros_sync_job(*, job_id: UUID, athlete_profile_id: UUID) -> None:
    """Exécute l'import COROS dans une session DB dédiée."""
    import json
    import logging
    import os
    from datetime import datetime, timedelta, timezone
    from sqlalchemy import select
    from opencoach.database.models import Activity, CorosSyncLock, IntegrationConnection
    from opencoach.database.session import SessionLocal
    from opencoach.integrations.coros.client import CorosMcpClient
    from opencoach.integrations.coros.errors import CorosMcpAuthenticationError
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
        config = dict(connection.config or {})
        checkpoint = dict(config.get("coros_sync_checkpoint") or {})
        # Ne basculer en incrémental qu’après un import initial ayant
        # réellement enregistré des activités. Une ancienne exécution
        # ayant importé uniquement les métriques ne doit pas tronquer l’historique.
        # A stale config flag must never skip the six-month import when no
        # COROS activities have actually been persisted.
        has_coros_activities = db.scalar(
            select(Activity.id)
            .where(
                Activity.athlete_profile_id == athlete_profile_id,
                Activity.provider == "coros",
            )
            .limit(1)
        ) is not None
        initial_import_completed = should_use_incremental_coros_sync(
            config,
            has_coros_activities,
        )
        checkpoint = prepare_coros_checkpoint(
            checkpoint,
            initial_import_completed=initial_import_completed,
        )
        incremental_start = (
            connection.last_synced_at.date() - timedelta(days=7)
            if initial_import_completed and connection.last_synced_at is not None
            else None
        )
        job_state = {
            "job_id": str(job_id),
            "status": "running",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "finished_at": None,
            "result": None,
            "error": None,
            "progress": {"category": None, "next_date": None},
        }
        connection.config = {**config, "coros_sync_job": job_state}
        db.commit()

        def save_checkpoint(category: str, next_date: str | None) -> None:
            current = dict((connection.config or {}).get("coros_sync_checkpoint") or {})
            completed = set(filter(None, current.get("_completed", "").split(",")))
            if next_date is None:
                current.pop(category, None)
                completed.add(category)
            else:
                current[category] = next_date
                completed.discard(category)
            current["_completed"] = ",".join(sorted(completed))
            state = dict((connection.config or {}).get("coros_sync_job") or job_state)
            state["progress"] = {"category": category, "next_date": next_date}
            connection.config = {
                **(connection.config or {}),
                "coros_sync_checkpoint": current,
                "coros_sync_job": state,
            }
            lock = db.get(CorosSyncLock, athlete_profile_id)
            if lock is not None and lock.job_id == str(job_id):
                lock.acquired_at = datetime.now(timezone.utc).replace(tzinfo=None)
            # Committe chaque fenêtre, l'état visible et le heartbeat du verrou.
            db.commit()

        result = CorosImportService(
            CorosMcpClient(refreshed["access_token"]),
            db,
            athlete_profile_id,
            progress_callback=save_checkpoint,
        ).import_history(
            config.get("categories", {}),
            months=6,
            start_date=incremental_start,
            checkpoint=checkpoint,
        )
        if refreshed != secret:
            connection.encrypted_secret = cipher.encrypt(json.dumps(refreshed, separators=(",", ":")))
        connection.config = {key: value for key, value in (connection.config or {}).items() if key != "coros_sync_checkpoint"}
        categories = config.get("categories", {})
        activities_enabled = categories.get("activities", True)
        imported_activities = result.get("imported_snapshots", {}).get("activities", 0)
        if activities_enabled and imported_activities > 0:
            connection.config = {**(connection.config or {}), "coros_initial_import_completed": True}
        elif activities_enabled:
            # Aucun résultat activité : conserver l’état initial pour que
            # la prochaine exécution retente toute la fenêtre de six mois.
            connection.config = {**(connection.config or {}), "coros_initial_import_completed": False}
        state = dict((connection.config or {}).get("coros_sync_job") or job_state)
        no_activities_error = (
            activities_enabled
            and imported_activities == 0
            and not initial_import_completed
        )
        state.update({
            "status": "error" if no_activities_error else "success",
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "result": result,
            "error": (
                "Aucune activité COROS n’a été importée sur la fenêtre initiale de six mois. "
                "L’historique reste à réessayer ; consulte les journaux pour vérifier querySportRecords."
                if no_activities_error else None
            ),
            "progress": {"category": None, "next_date": None},
        })
        connection.config = {**(connection.config or {}), "coros_sync_job": state}
        if not activities_enabled or imported_activities > 0:
            connection.last_synced_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.commit()
        if no_activities_error:
            COROS_SYNC_JOBS.failure(job_id, state["error"])
        else:
            COROS_SYNC_JOBS.success(job_id, result)
    except Exception as exc:
        db.rollback()
        authentication_error = isinstance(exc, CorosMcpAuthenticationError)
        logger.exception("Échec de la synchronisation COROS (job=%s, profile=%s)", job_id, athlete_profile_id)
        try:
            failed_connection = db.scalar(select(IntegrationConnection).where(
                IntegrationConnection.athlete_profile_id == athlete_profile_id,
                IntegrationConnection.provider == "coros",
            ))
            if failed_connection is not None:
                state = dict((failed_connection.config or {}).get("coros_sync_job") or {})
                if authentication_error:
                    failed_connection.enabled = False
                state.update({
                    "job_id": str(job_id),
                    "status": "error",
                    "finished_at": datetime.now(timezone.utc).isoformat(),
                    "http_status": 401 if authentication_error else 502,
                    "error": (
                        "La connexion COROS a expiré. Reconnecte ton compte."
                        if authentication_error
                        else "La synchronisation COROS a échoué. Vérifie la connexion puis consulte les journaux OpenCoach."
                    ),
                })
                failed_config = dict(failed_connection.config or {})
                if authentication_error:
                    failed_config["connected"] = False
                failed_connection.config = {**failed_config, "coros_sync_job": state}
                db.commit()
        except Exception:
            db.rollback()
            logger.exception("Impossible de sauvegarder l'état d'erreur COROS (job=%s)", job_id)
        # Ne jamais exposer à l'interface les détails internes, URL, jetons
        # ou réponses brutes renvoyés par le fournisseur.
        COROS_SYNC_JOBS.failure(job_id, "La synchronisation COROS a échoué. Vérifie la connexion puis consulte les journaux OpenCoach.")
    finally:
        try:
            lock = db.get(CorosSyncLock, athlete_profile_id)
            if lock is not None and lock.job_id == str(job_id):
                db.delete(lock)
                db.commit()
        except Exception:
            db.rollback()
            logger.exception("Impossible de libérer le verrou COROS (job=%s)", job_id)
        db.close()
