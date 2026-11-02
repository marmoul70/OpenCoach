from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from opencoach.authentication.dependencies import (
    get_current_athlete_profile_id,
)
from opencoach.database.models import IntegrationConnection
from opencoach.database.session import get_db
from opencoach.integrations.coros.client import CorosMcpClient
from opencoach.integrations.coros.tokens import refresh_secret_if_needed
from opencoach.integrations.coros.sync import CorosImportService
from opencoach.integrations.coros.errors import (
    CorosMcpAuthenticationError,
    CorosMcpError,
    CorosMcpProtocolError,
)
from opencoach.integrations.coros.oauth import (
    CorosOAuthClientService,
    CorosPendingLogin,
)
from opencoach.security import SecretCipher, SecretCipherError
from opencoach.services.coros_sync_job import COROS_SYNC_JOBS, run_coros_sync_job


router = APIRouter(
    prefix="/api/integrations/coros",
    tags=["integrations"],
)

DEFAULT_REDIRECT_URI = "http://127.0.0.1:43123/callback"
DEFAULT_CATEGORIES = {
    "activities": True,
    "activity_details": True,
    "fit_files": False,
    "sleep": True,
    "hrv": True,
    "heart_rate": True,
    "stress": True,
    "daily_health": True,
    "training_load": True,
}


class CorosSettingsUpdate(BaseModel):
    enabled: bool = True
    sync_interval_hours: int = Field(default=12, ge=0, le=24)
    categories: dict[str, bool]


def _cipher() -> SecretCipher:
    try:
        return SecretCipher.from_env()
    except SecretCipherError as exc:
        raise HTTPException(
            status_code=503,
            detail="La clé de chiffrement OpenCoach n'est pas configurée.",
        ) from exc


def _connection(
    db: Session,
    athlete_profile_id: UUID,
) -> IntegrationConnection | None:
    return db.scalar(
        select(IntegrationConnection).where(
            IntegrationConnection.athlete_profile_id == athlete_profile_id,
            IntegrationConnection.provider == "coros",
        )
    )


def _oauth() -> CorosOAuthClientService:
    return CorosOAuthClientService(
        redirect_uri=os.getenv(
            "OPENCOACH_COROS_REDIRECT_URI",
            DEFAULT_REDIRECT_URI,
        ),
    )


def _read_secret(
    connection: IntegrationConnection,
    cipher: SecretCipher,
) -> dict[str, Any]:
    if connection.encrypted_secret is None:
        return {}
    try:
        return json.loads(
            cipher.decrypt(connection.encrypted_secret)
        )
    except (SecretCipherError, ValueError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Impossible de lire les identifiants COROS chiffrés.",
        ) from exc


def _save_secret(
    connection: IntegrationConnection,
    cipher: SecretCipher,
    payload: dict[str, Any],
) -> None:
    connection.encrypted_secret = cipher.encrypt(
        json.dumps(payload, separators=(",", ":"))
    )


@router.get("/connection")
def get_coros_connection(
    athlete_profile_id: UUID = Depends(get_current_athlete_profile_id),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    connection = _connection(db, athlete_profile_id)
    if connection is None:
        return {
            "provider": "coros",
            "configured": False,
            "connected": False,
            "enabled": False,
            "last_synced_at": None,
            "sync_interval_hours": 12,
            "categories": DEFAULT_CATEGORIES,
            "initial_import_months": 6,
        }

    config = connection.config or {}
    return {
        "provider": "coros",
        "configured": True,
        "connected": bool(config.get("connected")),
        "enabled": connection.enabled,
        "last_synced_at": (
            connection.last_synced_at.isoformat()
            if connection.last_synced_at
            else None
        ),
        "sync_interval_hours": config.get("sync_interval_hours", 12),
        "categories": config.get("categories", DEFAULT_CATEGORIES),
        "initial_import_months": 6,
    }


@router.post("/oauth/start")
def start_coros_oauth(
    athlete_profile_id: UUID = Depends(get_current_athlete_profile_id),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    cipher = _cipher()
    try:
        pending = _oauth().begin_login()
    except CorosMcpError as exc:
        raise HTTPException(
            status_code=502,
            detail="Impossible de démarrer la connexion COROS.",
        ) from exc

    connection = _connection(db, athlete_profile_id)
    if connection is None:
        connection = IntegrationConnection(
            athlete_profile_id=athlete_profile_id,
            provider="coros",
            enabled=False,
            config={
                "athlete_id": "coros",
                "connected": False,
                "sync_interval_hours": 12,
                "categories": DEFAULT_CATEGORIES,
            },
        )
        db.add(connection)

    connection.config = {
        **(connection.config or {}),
        "athlete_id": "coros",
        "connected": False,
    }
    _save_secret(
        connection,
        cipher,
        {
            "status": "pending",
            "client_id": pending.client_id,
            "code_verifier": pending.code_verifier,
            "state": pending.state,
            "authorize_url": pending.authorize_url,
            "session_id": pending.session_id,
            "poll_token": pending.poll_token,
            "login_url": pending.login_url,
        },
    )
    db.commit()

    return {
        "login_url": pending.login_url,
        "status": "pending",
    }


@router.post("/oauth/poll")
def poll_coros_oauth(
    athlete_profile_id: UUID = Depends(get_current_athlete_profile_id),
    db: Session = Depends(get_db),
) -> dict[str, str | bool]:
    connection = _connection(db, athlete_profile_id)
    if connection is None or connection.encrypted_secret is None:
        raise HTTPException(
            status_code=409,
            detail="Aucune connexion COROS en attente.",
        )

    cipher = _cipher()
    secret = _read_secret(connection, cipher)
    if secret.get("status") == "connected":
        return {"connected": True, "status": "connected"}

    if secret.get("status") != "pending":
        raise HTTPException(
            status_code=409,
            detail="Aucune autorisation COROS en attente.",
        )

    pending = CorosPendingLogin(
        client_id=secret["client_id"],
        code_verifier=secret["code_verifier"],
        state=secret["state"],
        authorize_url=secret["authorize_url"],
        session_id=secret["session_id"],
        poll_token=secret["poll_token"],
        login_url=secret["login_url"],
    )

    oauth = _oauth()
    try:
        login_ticket = oauth.claim_login_ticket(pending)
        if login_ticket is None:
            return {"connected": False, "status": "pending"}

        tokens = oauth.exchange_login_ticket(
            pending,
            login_ticket,
        )
    except CorosMcpAuthenticationError as exc:
        raise HTTPException(
            status_code=401,
            detail="L'autorisation COROS a échoué ou a expiré.",
        ) from exc
    except CorosMcpProtocolError as exc:
        raise HTTPException(
            status_code=502,
            detail="La réponse d'authentification COROS est invalide.",
        ) from exc

    _save_secret(
        connection,
        cipher,
        {
            "status": "connected",
            "client_id": pending.client_id,
            "access_token": tokens.access_token,
            "refresh_token": tokens.refresh_token,
            "token_type": tokens.token_type,
            "scope": tokens.scope,
            "expires_at": (
                datetime.now(timezone.utc).timestamp()
                + tokens.expires_in
            ),
        },
    )
    connection.enabled = True
    connection.config = {
        **(connection.config or {}),
        "connected": True,
    }
    db.commit()

    return {"connected": True, "status": "connected"}


@router.put("/settings")
def update_coros_settings(
    payload: CorosSettingsUpdate,
    athlete_profile_id: UUID = Depends(get_current_athlete_profile_id),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    connection = _connection(db, athlete_profile_id)
    if connection is None:
        raise HTTPException(
            status_code=409,
            detail="Connecte d'abord ton compte COROS.",
        )

    current = connection.config or {}
    connection.enabled = payload.enabled
    connection.config = {
        **current,
        "sync_interval_hours": payload.sync_interval_hours,
        # Ne conserver que les catégories connues et compléter les nouvelles
        # préférences avec leurs valeurs par défaut (compatibilité UI/API).
        "categories": {
            key: bool(payload.categories.get(key, DEFAULT_CATEGORIES[key]))
            for key in DEFAULT_CATEGORIES
        },
    }
    db.commit()

    return {
        "enabled": connection.enabled,
        "sync_interval_hours": connection.config["sync_interval_hours"],
        "categories": connection.config["categories"],
    }


@router.post("/test")
def test_coros_connection(
    athlete_profile_id: UUID = Depends(get_current_athlete_profile_id),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Vérifie le renouvellement OAuth et l'accès au serveur MCP."""
    connection = _connection(db, athlete_profile_id)
    if connection is None or not connection.enabled:
        raise HTTPException(status_code=409, detail="Connecte d'abord ton compte COROS.")
    cipher = _cipher()
    secret = _read_secret(connection, cipher)
    if secret.get("status") != "connected":
        raise HTTPException(status_code=409, detail="La connexion COROS doit être réautorisée.")
    try:
        refreshed = refresh_secret_if_needed(secret, _oauth(), now=datetime.now(timezone.utc).timestamp())
        tools = CorosMcpClient(refreshed["access_token"]).list_tools()
    except CorosMcpAuthenticationError as exc:
        connection.enabled = False
        connection.config = {**(connection.config or {}), "connected": False}
        db.commit()
        raise HTTPException(status_code=401, detail="La connexion COROS a expiré. Reconnecte ton compte.") from exc
    except CorosMcpError as exc:
        raise HTTPException(status_code=502, detail="Le serveur COROS MCP est temporairement indisponible.") from exc
    if refreshed != secret:
        _save_secret(connection, cipher, refreshed)
    db.commit()
    return {"connected": True, "mcp_reachable": True, "available_tools": [tool.get("name") for tool in tools if tool.get("name")], "available_tools_count": len(tools)}


@router.post("/sync")
def sync_coros_history(
    athlete_profile_id: UUID = Depends(get_current_athlete_profile_id),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Lance un import idempotent de l'historique COROS disponible."""
    connection = _connection(db, athlete_profile_id)
    if connection is None or not connection.enabled:
        raise HTTPException(status_code=409, detail="Connecte d'abord ton compte COROS.")
    cipher = _cipher()
    secret = _read_secret(connection, cipher)
    if secret.get("status") != "connected":
        raise HTTPException(status_code=409, detail="La connexion COROS doit être réautorisée.")
    try:
        refreshed = refresh_secret_if_needed(secret, _oauth(), now=datetime.now(timezone.utc).timestamp())
        client = CorosMcpClient(refreshed["access_token"])
        result = CorosImportService(client, db, athlete_profile_id).import_history(
            (connection.config or {}).get("categories", DEFAULT_CATEGORIES),
            months=6,
        )
    except CorosMcpAuthenticationError as exc:
        connection.enabled = False
        connection.config = {**(connection.config or {}), "connected": False}
        db.commit()
        raise HTTPException(status_code=401, detail="La connexion COROS a expiré. Reconnecte ton compte.") from exc
    except CorosMcpError as exc:
        db.rollback()
        raise HTTPException(status_code=502, detail="L'import COROS a échoué : le serveur MCP est indisponible ou a retourné une réponse invalide.") from exc
    if refreshed != secret:
        _save_secret(connection, cipher, refreshed)
    connection.last_synced_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()
    return {"status": "completed", **result}


@router.post("/sync/start")
def start_coros_sync(
    background_tasks: BackgroundTasks,
    athlete_profile_id: UUID = Depends(get_current_athlete_profile_id),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    connection = _connection(db, athlete_profile_id)
    if connection is None or not connection.enabled:
        raise HTTPException(status_code=409, detail="Connecte d'abord ton compte COROS.")
    active = COROS_SYNC_JOBS.find_active(athlete_profile_id)
    if active is not None:
        return {"job_id": str(active.id), "status": active.status}
    job = COROS_SYNC_JOBS.create(athlete_profile_id)
    background_tasks.add_task(run_coros_sync_job, job_id=job.id, athlete_profile_id=athlete_profile_id)
    return {"job_id": str(job.id), "status": job.status}


@router.get("/sync/status/{job_id}")
def get_coros_sync_status(
    job_id: UUID,
    athlete_profile_id: UUID = Depends(get_current_athlete_profile_id),
) -> dict[str, Any]:
    job = COROS_SYNC_JOBS.get(job_id)
    if job is None or job.athlete_profile_id != athlete_profile_id:
        raise HTTPException(status_code=404, detail="Import COROS introuvable.")
    return {
        "job_id": str(job.id),
        "status": job.status,
        "created_at": job.created_at.isoformat(),
        "finished_at": job.finished_at.isoformat() if job.finished_at else None,
        "result": job.result,
        "error": job.error,
    }
