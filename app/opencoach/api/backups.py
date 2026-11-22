from __future__ import annotations

import json
import logging
import os
import signal

from datetime import date, datetime, timedelta
from typing import Literal
from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    HTTPException,
    Request,
)
from fastapi.responses import (
    FileResponse,
    Response,
)
from pydantic import BaseModel

from opencoach.backup import (
    BackupInfo,
    BackupRestoreService,
    BackupService,
)
from opencoach.database.session import (
    PROJECT_ROOT,
    SessionLocal,
    engine,
)
from opencoach.database.models.user import User
from opencoach.database.models.athlete_profile import AthleteProfile as AthleteProfileModel
from opencoach.database.repositories.sql_profile import SqlProfileRepository
from opencoach.database.repositories import SqlTrainingSessionRepository
from opencoach.api.coaching.dependencies import (
    build_weekly_planning_services_for_user,
)
from sqlalchemy import select


router = APIRouter(
    prefix="/api/backups",
    tags=[
        "backups",
    ],
)


logger = logging.getLogger(__name__)


STATUS_PATH = (
    PROJECT_ROOT
    / "data"
    / "backups"
    / "backup-status.json"
)


class BackupResponse(BaseModel):
    filename: str
    created_at: datetime
    size_bytes: int


class BackupStatusResponse(BaseModel):
    status: Literal[
        "success",
        "failed",
        "unknown",
    ]

    executed_at: datetime | None
    filename: str | None
    error: str | None


class BackupRestoreResponse(BaseModel):
    restored: bool
    safety_backup_filename: str
    imported_revision: str
    environment_restored: bool = False
    planning_status: Literal[
        "generated",
        "already_present",
        "skipped",
        "failed",
    ] = "skipped"
    planning_session_count: int = 0
    planning_message: str | None = None


def _restart_backend_after_response() -> None:
    os.kill(os.getpid(), signal.SIGTERM)


def _service() -> BackupService:
    return BackupService()


def _restore_service() -> BackupRestoreService:
    return BackupRestoreService(
        backup_service=_service()
    )


def _planning_profile_skip_reason(training) -> str | None:
    """Vérifie les deux paramètres indispensables au placement hebdomadaire."""
    available_days = training.available_days or []
    weekly_sessions = training.weekly_sessions
    if (
        weekly_sessions is None
        or weekly_sessions < 1
        or weekly_sessions > 7
        or not available_days
        or any(
            not isinstance(day, int) or day < 0 or day > 6
            for day in available_days
        )
    ):
        return (
            "Planning non généré : renseigne le nombre de séances hebdomadaires "
            "et au moins un jour d'entraînement valide dans le profil."
        )
    return None


def _restore_training_planning(
    request: Request,
) -> tuple[
    Literal["generated", "already_present", "skipped", "failed"],
    int,
    str,
]:
    """Reconstruit les semaines absentes après restauration, si le profil le permet.

    La restauration des données reste acquise même si le profil ne permet
    pas de planifier ou si le moteur de génération rencontre une erreur.
    """
    db = SessionLocal()
    try:
        raw_user_id = getattr(request.state, "user_id", None)
        user_id = None
        if raw_user_id:
            try:
                candidate = UUID(str(raw_user_id))
                if db.scalar(
                    select(AthleteProfileModel.id).where(
                        AthleteProfileModel.user_id == candidate
                    )
                ) is not None:
                    user_id = candidate
            except (TypeError, ValueError):
                user_id = None

        if user_id is None:
            restored_user_ids = set(
                db.scalars(
                    select(AthleteProfileModel.user_id)
                ).all()
            )
            if len(restored_user_ids) != 1:
                return (
                    "skipped",
                    0,
                    "Planning non généré : impossible d'identifier un profil athlète unique.",
                )
            user_id = next(iter(restored_user_ids))

        profile_id = db.scalar(
            select(AthleteProfileModel.id).where(
                AthleteProfileModel.user_id == user_id
            )
        )
        if profile_id is None:
            return (
                "skipped",
                0,
                "Planning non généré : aucun profil athlète n'est présent dans la sauvegarde.",
            )

        profile = SqlProfileRepository(db, user_id).get_profile()
        training = profile.training
        skip_reason = _planning_profile_skip_reason(training)
        if skip_reason is not None:
            return ("skipped", 0, skip_reason)

        context_builder, generation_service = (
            build_weekly_planning_services_for_user(
                db=db,
                user_id=user_id,
            )
        )
        training_repository = SqlTrainingSessionRepository(db)

        today = date.today()
        current_monday = today - timedelta(days=today.weekday())
        target_weeks = (
            current_monday,
            current_monday + timedelta(days=7),
        )

        generated_count = 0
        already_planned_weeks = 0

        for week_start in target_weeks:
            week_end = week_start + timedelta(days=6)
            existing_sessions = training_repository.list_sessions_between(
                profile_id,
                week_start,
                week_end,
            )
            if any(
                session.status == "planned"
                for session in existing_sessions
            ):
                already_planned_weeks += 1
                continue

            planning_date = max(today, week_start)
            prepared = context_builder.build(
                athlete_profile_id=profile_id,
                planning_date=planning_date,
                trajectory_start_date=current_monday,
            )
            result = generation_service.execute(
                athlete_profile_id=profile_id,
                planning_input=prepared.planning_input,
                physiological_reference_date=planning_date,
                sport_disciplines=prepared.sport_disciplines,
                reconcile_from_date=planning_date,
                additional_context=(
                    "Planning reconstruit automatiquement après restauration d'une sauvegarde.",
                ),
            )
            generated_count += result.session_count

        if generated_count:
            return (
                "generated",
                generated_count,
                f"Planning reconstruit après restauration : {generated_count} séance(s) créée(s) sur les deux semaines à venir.",
            )
        if already_planned_weeks:
            return (
                "already_present",
                0,
                "Aucune reconstruction nécessaire : des séances planifiées sont déjà présentes dans la période contrôlée.",
            )
        return (
            "skipped",
            0,
            "Le profil est complet, mais le moteur n'a proposé aucune séance sur les deux semaines contrôlées.",
        )

    except Exception:
        logger.exception(
            "La sauvegarde a été restaurée, mais la reconstruction du planning a échoué."
        )
        return (
            "failed",
            0,
            "La sauvegarde est restaurée, mais la reconstruction du planning a échoué. Consulte les journaux du backend.",
        )
    finally:
        db.close()


def _to_response(
    backup: BackupInfo,
) -> BackupResponse:
    return BackupResponse(
        filename=backup.filename,
        created_at=backup.created_at,
        size_bytes=backup.size_bytes,
    )


@router.get(
    "",
    response_model=list[BackupResponse],
)
def list_backups() -> list[BackupResponse]:
    service = _service()

    return [
        _to_response(
            backup
        )
        for backup
        in service.list_backups()
    ]


@router.post(
    "",
    response_model=BackupResponse,
)
def create_backup() -> BackupResponse:
    service = _service()

    try:
        backup = (
            service.create_backup()
        )

    except (
        FileNotFoundError,
        RuntimeError,
    ) as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc

    return _to_response(
        backup
    )


@router.get(
    "/status",
    response_model=BackupStatusResponse,
)
def get_backup_status() -> BackupStatusResponse:
    if not STATUS_PATH.is_file():
        return BackupStatusResponse(
            status="unknown",
            executed_at=None,
            filename=None,
            error=None,
        )

    try:
        payload = json.loads(
            STATUS_PATH.read_text(
                encoding="utf-8",
            )
        )

        return BackupStatusResponse(
            status=payload.get(
                "status",
                "unknown",
            ),
            executed_at=payload.get(
                "executed_at",
            ),
            filename=payload.get(
                "filename",
            ),
            error=payload.get(
                "error",
            ),
        )

    except (
        OSError,
        json.JSONDecodeError,
        ValueError,
    ):
        return BackupStatusResponse(
            status="unknown",
            executed_at=None,
            filename=None,
            error=None,
        )


@router.post(
    "/restore",
    response_model=BackupRestoreResponse,
)
async def restore_uploaded_backup(
    request: Request,
    background_tasks: BackgroundTasks,
) -> BackupRestoreResponse:
    content_type = (
        request.headers.get(
            "content-type",
            ""
        )
    )

    allowed = (
        "application/zip"
        in content_type
        or "application/octet-stream"
        in content_type
    )

    if not allowed:
        raise HTTPException(
            status_code=415,
            detail=(
                "Un fichier ZIP OpenCoach "
                "est attendu."
            ),
        )

    # En accès public uniquement tant qu'aucun compte n'existe.
    db = SessionLocal()
    try:
        has_users = db.scalar(select(User.id).limit(1)) is not None
    finally:
        db.close()

    if has_users and not getattr(request.state, "user_id", None):
        raise HTTPException(status_code=401, detail="Connectez-vous pour restaurer une sauvegarde.")

    archive = await request.body()
    service = (
        _restore_service()
    )

    try:
        # Ferme les connexions SQLAlchemy
        # actuellement dans le pool.
        engine.dispose()

        result = (
            service.restore_archive_bytes(
                archive
            )
        )

        engine.dispose()

    except (
        ValueError,
        RuntimeError,
        FileNotFoundError,
    ) as exc:
        engine.dispose()

        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    planning_status, planning_session_count, planning_message = (
        _restore_training_planning(request)
    )
    engine.dispose()

    if result.environment_restored:
        background_tasks.add_task(_restart_backend_after_response)

    return BackupRestoreResponse(
        restored=True,
        safety_backup_filename=result.safety_backup.filename,
        imported_revision=result.imported_revision,
        environment_restored=result.environment_restored,
        planning_status=planning_status,
        planning_session_count=planning_session_count,
        planning_message=planning_message,
    )


@router.post(
    "/{filename}/restore",
    response_model=BackupRestoreResponse,
)
def restore_existing_backup(
    filename: str,
    request: Request,
    background_tasks: BackgroundTasks,
) -> BackupRestoreResponse:
    service = (
        _restore_service()
    )

    try:
        engine.dispose()

        result = (
            service.restore_existing_backup(
                filename
            )
        )

        engine.dispose()

    except ValueError as exc:
        engine.dispose()

        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except FileNotFoundError as exc:
        engine.dispose()

        raise HTTPException(
            status_code=404,
            detail="Sauvegarde introuvable.",
        ) from exc

    except RuntimeError as exc:
        engine.dispose()

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc

    planning_status, planning_session_count, planning_message = (
        _restore_training_planning(request)
    )
    engine.dispose()

    if result.environment_restored:
        background_tasks.add_task(_restart_backend_after_response)

    return BackupRestoreResponse(
        restored=True,
        safety_backup_filename=result.safety_backup.filename,
        imported_revision=result.imported_revision,
        environment_restored=result.environment_restored,
        planning_status=planning_status,
        planning_session_count=planning_session_count,
        planning_message=planning_message,
    )


@router.delete(
    "/{filename}",
    status_code=204,
)
def delete_backup(
    filename: str,
) -> Response:
    service = _service()

    try:
        path = (
            service.get_backup_path(
                filename
            )
        )

        path.unlink()

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail="Sauvegarde introuvable.",
        ) from exc

    return Response(
        status_code=204
    )


@router.get(
    "/{filename}/download",
)
def download_backup(
    filename: str,
) -> FileResponse:
    service = _service()

    try:
        path = (
            service.get_backup_path(
                filename
            )
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail="Sauvegarde introuvable.",
        ) from exc

    return FileResponse(
        path=path,
        filename=path.name,
        media_type="application/zip",
    )
