from __future__ import annotations

import json

from datetime import datetime
from typing import Literal

from fastapi import (
    APIRouter,
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
    engine,
)


router = APIRouter(
    prefix="/api/backups",
    tags=[
        "backups",
    ],
)


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


def _service() -> BackupService:
    return BackupService()


def _restore_service() -> BackupRestoreService:
    return BackupRestoreService(
        backup_service=_service()
    )


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

    archive = (
        await request.body()
    )

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

    return BackupRestoreResponse(
        restored=True,
        safety_backup_filename=(
            result
            .safety_backup
            .filename
        ),
        imported_revision=(
            result.imported_revision
        ),
    )


@router.post(
    "/{filename}/restore",
    response_model=BackupRestoreResponse,
)
def restore_existing_backup(
    filename: str,
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

    return BackupRestoreResponse(
        restored=True,
        safety_backup_filename=(
            result
            .safety_backup
            .filename
        ),
        imported_revision=(
            result.imported_revision
        ),
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
