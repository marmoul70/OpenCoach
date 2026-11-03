"""Synchronisation automatique COROS selon la fréquence configurée."""

from __future__ import annotations

from dataclasses import dataclass
import os
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from opencoach.database.models import (
    AthleteProfile,
    CorosSyncLock,
    IntegrationConnection,
    User,
)
from opencoach.database.session import SessionLocal
from opencoach.services.coros_sync_job import run_coros_sync_job


PROVIDER = "coros"
STALE_LOCK_AFTER = timedelta(minutes=30)


@dataclass(frozen=True, slots=True)
class CorosSyncTarget:
    athlete_profile_id: UUID
    interval_hours: int
    last_synced_at: datetime | None


def is_sync_due(
    *,
    now: datetime,
    interval_hours: int,
    last_synced_at: datetime | None,
) -> bool:
    """Indique si une connexion doit être synchronisée.

    Une fréquence nulle désactive l'automatisation. Une connexion
    jamais synchronisée est immédiatement éligible.
    """
    if interval_hours <= 0:
        return False
    if last_synced_at is None:
        return True
    current = now.replace(tzinfo=None) if now.tzinfo else now
    previous = (
        last_synced_at.replace(tzinfo=None)
        if last_synced_at.tzinfo
        else last_synced_at
    )
    return current - previous >= timedelta(hours=interval_hours)


def list_due_targets(session, *, now: datetime) -> list[CorosSyncTarget]:
    statement = (
        select(
            AthleteProfile.id,
            IntegrationConnection.config,
            IntegrationConnection.last_synced_at,
        )
        .join(User, User.id == AthleteProfile.user_id)
        .join(
            IntegrationConnection,
            IntegrationConnection.athlete_profile_id == AthleteProfile.id,
        )
        .where(
            User.active.is_(True),
            IntegrationConnection.provider == PROVIDER,
            IntegrationConnection.enabled.is_(True),
            IntegrationConnection.encrypted_secret.is_not(None),
        )
        .order_by(User.created_at)
    )
    targets: list[CorosSyncTarget] = []
    for profile_id, config, last_synced_at in session.execute(statement):
        interval = int((config or {}).get("sync_interval_hours", 12))
        if is_sync_due(
            now=now,
            interval_hours=interval,
            last_synced_at=last_synced_at,
        ):
            targets.append(CorosSyncTarget(profile_id, interval, last_synced_at))
    return targets


def _worker_is_alive(pid: object) -> bool:
    """Return conservatively whether a persisted worker PID may still be active."""
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except (PermissionError, OSError):
        # An OS error other than ESRCH is not proof that the process is gone.
        return True
    return True


def _acquire_lock(session, *, profile_id: UUID, job_id: UUID, now: datetime) -> bool:
    lock = session.get(CorosSyncLock, profile_id)
    if lock is not None:
        acquired = lock.acquired_at
        if now - acquired > STALE_LOCK_AFTER:
            connection = session.scalar(select(IntegrationConnection).where(
                IntegrationConnection.athlete_profile_id == profile_id,
                IntegrationConnection.provider == PROVIDER,
            ))
            state = ((connection.config or {}).get("coros_sync_job") or {}) if connection else {}
            same_active_job = (
                state.get("job_id") == lock.job_id
                and state.get("status") in {"pending", "running"}
            )
            if same_active_job and _worker_is_alive(state.get("worker_pid")):
                return False
            session.delete(lock)
            session.commit()
        else:
            return False
    session.add(CorosSyncLock(
        athlete_profile_id=profile_id,
        job_id=str(job_id),
        acquired_at=now,
    ))
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        return False
    return True


def main() -> int:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    with SessionLocal() as session:
        targets = list_due_targets(session, now=now)

    if not targets:
        print("[INFO] Aucune synchronisation COROS à effectuer.")
        return 0

    print(f"[INFO] {len(targets)} profil(s) COROS éligible(s).")
    failures = 0
    for target in targets:
        job_id = uuid4()
        with SessionLocal() as session:
            if not _acquire_lock(
                session,
                profile_id=target.athlete_profile_id,
                job_id=job_id,
                now=now,
            ):
                print(f"[INFO] Import déjà actif pour {target.athlete_profile_id}.")
                continue
            connection = session.scalar(select(IntegrationConnection).where(
                IntegrationConnection.athlete_profile_id == target.athlete_profile_id,
                IntegrationConnection.provider == PROVIDER,
            ))
            if connection is None:
                session.delete(session.get(CorosSyncLock, target.athlete_profile_id))
                session.commit()
                continue
            connection.config = {
                **(connection.config or {}),
                "coros_sync_job": {
                    "job_id": str(job_id),
                    "status": "pending",
                    "created_at": now.replace(tzinfo=timezone.utc).isoformat(),
                    "finished_at": None,
                    "result": None,
                    "error": None,
                    "progress": {"category": None, "next_date": None},
                },
            }
            session.commit()

        print(f"[INFO] Synchronisation COROS du profil {target.athlete_profile_id}.")
        run_coros_sync_job(
            job_id=job_id,
            athlete_profile_id=target.athlete_profile_id,
        )
        with SessionLocal() as session:
            connection = session.scalar(select(IntegrationConnection).where(
                IntegrationConnection.athlete_profile_id == target.athlete_profile_id,
                IntegrationConnection.provider == PROVIDER,
            ))
            status = ((connection.config or {}).get("coros_sync_job") or {}).get("status") if connection else "missing"
        if status != "success":
            failures += 1
            print(f"[ERREUR] Synchronisation COROS en échec pour {target.athlete_profile_id}.")
        else:
            print(f"[OK] Synchronisation COROS terminée pour {target.athlete_profile_id}.")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
