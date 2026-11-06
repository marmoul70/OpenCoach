from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from opencoach.authentication.dependencies import (
    get_current_athlete_profile_id,
)
from opencoach.database.models import CorosSyncLock, IntegrationConnection
from opencoach.database.session import get_db
from opencoach.database.repositories.sql_training_session import (
    SqlTrainingSessionRepository,
)
from opencoach.integrations.coros.client import CorosMcpClient
from opencoach.integrations.coros.tokens import refresh_secret_if_needed
from opencoach.integrations.coros.errors import (
    CorosMcpAuthenticationError,
    CorosMcpError,
    CorosMcpProtocolError,
    CorosMcpToolError,
)
from opencoach.integrations.coros.workout_mapper import (
    CorosWorkoutMappingError,
    map_training_session_to_coros,
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


class CorosWorkoutPushRequest(BaseModel):
    confirmed_no_duplicate: bool = False


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


def _recover_interrupted_coros_sync(
    db: Session,
    athlete_profile_id: UUID,
    connection: IntegrationConnection | None,
) -> None:
    """Mark a persisted job interrupted when its in-process worker no longer exists."""
    if connection is None:
        return

    state = dict((connection.config or {}).get("coros_sync_job") or {})
    if state.get("status") not in {"pending", "running"}:
        return

    raw_job_id = state.get("job_id")
    try:
        job_id = UUID(str(raw_job_id))
    except (TypeError, ValueError):
        job_id = None

    # PID lets multiple API workers distinguish a live job owned by another
    # process from a job left behind by a server restart.
    worker_pid = state.get("worker_pid")
    if isinstance(worker_pid, int) and worker_pid > 0:
        try:
            os.kill(worker_pid, 0)
            return
        except PermissionError:
            return
        except ProcessLookupError:
            # The worker process is definitively gone.
            pass
        except OSError:
            # An unexpected OS error is not proof that the worker stopped.
            # Keep the lock; a later status check can retry recovery safely.
            return
    elif job_id is not None and COROS_SYNC_JOBS.get(job_id) is not None:
        return

    state.update({
        "status": "interrupted",
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "error": (
            "La synchronisation COROS a été interrompue par un arrêt du serveur. "
            "Relance-la pour reprendre au dernier point sauvegardé."
        ),
    })
    connection.config = {
        **(connection.config or {}),
        "coros_sync_job": state,
    }

    lock = db.get(CorosSyncLock, athlete_profile_id)
    if lock is not None and lock.job_id == str(raw_job_id):
        db.delete(lock)
    db.commit()


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
            "sync_job": None,
        }

    _recover_interrupted_coros_sync(db, athlete_profile_id, connection)
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
        "sync_job": config.get("coros_sync_job"),
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
    return {
        "connected": True,
        "mcp_reachable": True,
        "available_tools": [
            {
                "name": tool.get("name"),
                "description": tool.get("description", ""),
                "input_schema": tool.get("inputSchema", {}),
            }
            for tool in tools
            if tool.get("name")
        ],
        "available_tools_count": len(tools),
    }


@router.post("/workouts/{session_id}/push")
def push_training_session_to_coros(
    session_id: UUID,
    payload: CorosWorkoutPushRequest,
    athlete_profile_id: UUID = Depends(get_current_athlete_profile_id),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Ajoute une séance OpenCoach planifiée au calendrier COROS."""
    repository = SqlTrainingSessionRepository(db)
    training_session = repository.get_session(
        athlete_profile_id,
        session_id,
    )
    if training_session is None:
        raise HTTPException(status_code=404, detail="Séance introuvable.")

    try:
        workout_payload = map_training_session_to_coros(training_session)
    except CorosWorkoutMappingError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    current_status = training_session.coros_sync_status
    if current_status == "synced":
        if training_session.coros_payload_hash == workout_payload.payload_hash:
            return {
                "status": "synced",
                "last_synced_at": (
                    training_session.coros_last_synced_at.isoformat()
                    if training_session.coros_last_synced_at
                    else None
                ),
                "message": "Cette séance est déjà présente dans ton calendrier COROS.",
            }
        raise HTTPException(
            status_code=409,
            detail=(
                "Cette séance a déjà été envoyée à COROS puis modifiée dans OpenCoach. "
                "La mise à jour d'une séance déjà envoyée sera ajoutée dans une évolution "
                "ultérieure ; aucun doublon n'a été créé."
            ),
        )

    if current_status == "pending":
        stale_pending = _coros_push_is_stale(
            training_session.coros_sync_started_at
        )
        if not stale_pending:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Un envoi COROS est encore en cours. Attends sa fin avant "
                    "de relancer cette opération."
                ),
            )
        if not payload.confirmed_no_duplicate:
            raise HTTPException(
                status_code=409,
                detail=(
                    "L'envoi COROS est bloqué depuis plus de cinq minutes. "
                    "Vérifie le calendrier COROS. Si la séance est absente, "
                    "confirme cette vérification pour autoriser une nouvelle tentative."
                ),
            )

    if current_status == "unknown" and not payload.confirmed_no_duplicate:
        raise HTTPException(
            status_code=409,
            detail=(
                "Le résultat du précédent envoi n'a pas pu être confirmé. "
                "Vérifie d'abord le calendrier COROS. Si la séance n'y figure pas, "
                "confirme cette vérification pour autoriser un nouvel envoi."
            ),
        )

    connection = _connection(db, athlete_profile_id)
    if connection is None or not connection.enabled:
        raise HTTPException(
            status_code=409,
            detail="Connecte et active d'abord ton compte COROS.",
        )

    cipher = _cipher()
    secret = _read_secret(connection, cipher)
    if secret.get("status") != "connected":
        raise HTTPException(
            status_code=409,
            detail="La connexion COROS doit être réautorisée.",
        )

    try:
        refreshed = refresh_secret_if_needed(
            secret,
            _oauth(),
            now=datetime.now(timezone.utc).timestamp(),
        )
        if refreshed != secret:
            _save_secret(connection, cipher, refreshed)
            db.commit()

        client = CorosMcpClient(refreshed["access_token"])
        tools = client.list_tools()
    except CorosMcpAuthenticationError as exc:
        connection.enabled = False
        connection.config = {
            **(connection.config or {}),
            "connected": False,
        }
        db.commit()
        raise HTTPException(
            status_code=401,
            detail="La connexion COROS a expiré. Reconnecte ton compte.",
        ) from exc
    except CorosMcpError as exc:
        raise HTTPException(
            status_code=502,
            detail="Le serveur COROS MCP est temporairement indisponible.",
        ) from exc

    create_tool = next(
        (
            tool for tool in tools
            if tool.get("name") == "createScheduledWorkout"
        ),
        None,
    )
    if create_tool is None:
        raise HTTPException(
            status_code=409,
            detail=(
                "La connexion COROS actuelle ne propose pas la création "
                "de séances planifiées. Actualise les outils MCP ou réessaie "
                "après une mise à jour du service COROS."
            ),
        )

    input_schema = create_tool.get("inputSchema")
    required = (
        set(input_schema.get("required", []))
        if isinstance(input_schema, dict)
        else set()
    )
    if not {"date", "course"}.issubset(required):
        raise HTTPException(
            status_code=502,
            detail=(
                "Le schéma createScheduledWorkout fourni par COROS "
                "est incompatible avec cette version d'OpenCoach."
            ),
        )

    # Réservation atomique : deux requêtes simultanées ne peuvent pas
    # toutes les deux passer de l'état libre à pending.
    started_at = datetime.now(timezone.utc)
    claimed = repository.claim_coros_workout_push(
        athlete_profile_id,
        session_id,
        workout_payload.payload_hash,
        started_at,
        allow_uncertain=payload.confirmed_no_duplicate,
    )
    if not claimed:
        raise HTTPException(
            status_code=409,
            detail=(
                "Une autre requête a déjà réservé l'envoi de cette séance. "
                "Actualise la page avant de réessayer."
            ),
        )
    training_session = repository.get_session(
        athlete_profile_id,
        session_id,
    )
    if training_session is None:
        raise HTTPException(
            status_code=404,
            detail="Séance introuvable après réservation de l'envoi COROS.",
        )
    # La réservation SQL est une mise à jour atomique avec
    # synchronize_session=False : réconcilier explicitement l'objet ORM
    # chargé avant la réservation pour ne pas réécrire un ancien hash.
    training_session.coros_sync_status = "pending"
    training_session.coros_sync_started_at = started_at
    training_session.coros_payload_hash = workout_payload.payload_hash
    training_session.coros_sync_error = None

    try:
        result = client.call_tool(
            "createScheduledWorkout",
            workout_payload.as_tool_arguments(),
        )
    except CorosMcpAuthenticationError as exc:
        training_session.coros_sync_status = "failed"
        training_session.coros_sync_started_at = None
        training_session.coros_sync_error = (
            "La connexion COROS a été refusée. Reconnecte ton compte avant de réessayer."
        )
        repository.save_session(athlete_profile_id, training_session)
        connection.enabled = False
        connection.config = {
            **(connection.config or {}),
            "connected": False,
        }
        db.commit()
        raise HTTPException(
            status_code=401,
            detail=training_session.coros_sync_error,
        ) from exc
    except CorosMcpToolError as exc:
        training_session.coros_sync_status = "failed"
        training_session.coros_sync_started_at = None
        training_session.coros_sync_error = str(exc)[:2000]
        repository.save_session(athlete_profile_id, training_session)
        raise HTTPException(
            status_code=422,
            detail=training_session.coros_sync_error,
        ) from exc
    except CorosMcpProtocolError as exc:
        training_session.coros_sync_status = "unknown"
        training_session.coros_sync_started_at = None
        training_session.coros_sync_error = (
            "COROS n'a pas confirmé le résultat de l'envoi. "
            "Vérifie le calendrier COROS avant toute nouvelle tentative."
        )
        repository.save_session(athlete_profile_id, training_session)
        raise HTTPException(
            status_code=502,
            detail=training_session.coros_sync_error,
        ) from exc
    except CorosMcpError as exc:
        training_session.coros_sync_status = "unknown"
        training_session.coros_sync_error = (
            "Le résultat de l'envoi est incertain. "
            "Vérifie le calendrier COROS avant toute nouvelle tentative."
        )
        repository.save_session(athlete_profile_id, training_session)
        raise HTTPException(
            status_code=502,
            detail=training_session.coros_sync_error,
        ) from exc

    now = datetime.now(timezone.utc)
    training_session.coros_sync_status = "synced"
    training_session.coros_sync_started_at = None
    training_session.coros_last_synced_at = now
    training_session.coros_sync_error = None
    training_session.coros_workout_id = _extract_coros_scheduled_id(result)
    saved_session = repository.save_session(
        athlete_profile_id,
        training_session,
    )
    other_workouts = _extract_other_coros_workouts(
        result,
        created_id=saved_session.coros_workout_id,
        current_name=saved_session.title,
    )
    message = (
        f"« {saved_session.title} » a été ajoutée au calendrier COROS "
        f"du {saved_session.date.strftime('%d/%m/%Y')}. "
        "Synchronise ensuite ta montre avec l'application COROS."
    )
    if other_workouts:
        message += (
            " Autres séances déjà présentes ce jour : "
            + ", ".join(other_workouts)
            + "."
        )

    return {
        "status": "synced",
        "last_synced_at": (
            saved_session.coros_last_synced_at.isoformat()
            if saved_session.coros_last_synced_at
            else now.isoformat()
        ),
        "message": message,
        "other_workouts": other_workouts,
    }


def _coros_push_is_stale(
    started_at: datetime | None,
    *,
    now: datetime | None = None,
) -> bool:
    """Autorise une réconciliation manuelle seulement après un délai de sécurité."""
    if started_at is None:
        return True
    current_time = now or datetime.now(timezone.utc)
    normalized_start = (
        started_at.replace(tzinfo=timezone.utc)
        if started_at.tzinfo is None
        else started_at
    )
    return current_time - normalized_start >= timedelta(minutes=5)


def _extract_coros_scheduled_id(result: dict[str, Any]) -> str | None:
    """Récupère idInPlan sans dépendre d'un format de réponse unique."""
    candidates: list[Any] = []
    structured = result.get("structuredContent")
    if structured is not None:
        candidates.append(structured)

    for item in result.get("content", []):
        if not isinstance(item, dict) or item.get("type") != "text":
            continue
        raw_text = item.get("text")
        if not isinstance(raw_text, str):
            continue
        try:
            candidates.append(json.loads(raw_text))
        except ValueError:
            object_start = raw_text.find("{")
            object_end = raw_text.rfind("}")
            if object_start >= 0 and object_end > object_start:
                try:
                    candidates.append(
                        json.loads(raw_text[object_start:object_end + 1])
                    )
                except ValueError:
                    pass

    for candidate in candidates:
        found = _find_coros_id(candidate)
        if found:
            return found
    return None


def _extract_other_coros_workouts(
    result: dict[str, Any],
    *,
    created_id: str | None,
    current_name: str,
) -> list[str]:
    """Retourne les autres séances du jour éventuellement incluses dans le résultat."""
    candidates: list[Any] = []
    structured = result.get("structuredContent")
    if structured is not None:
        candidates.append(structured)
    for item in result.get("content", []):
        if not isinstance(item, dict) or item.get("type") != "text":
            continue
        raw_text = item.get("text")
        if not isinstance(raw_text, str):
            continue
        try:
            candidates.append(json.loads(raw_text))
        except ValueError:
            continue

    found: list[str] = []
    current_normalized = current_name.strip().casefold()
    for candidate in candidates:
        for workout_id, name in _collect_coros_workout_names(candidate):
            if created_id is not None and workout_id == created_id:
                continue
            if name.strip().casefold() == current_normalized:
                continue
            if name not in found:
                found.append(name)
    return found


def _collect_coros_workout_names(value: Any) -> list[tuple[str | None, str]]:
    collected: list[tuple[str | None, str]] = []
    if isinstance(value, dict):
        workout_id = value.get("idInPlan", value.get("id_in_plan"))
        name = (
            value.get("courseName")
            or value.get("workoutName")
            or value.get("name")
            or value.get("title")
        )
        if isinstance(name, str) and name.strip():
            collected.append(
                (str(workout_id) if workout_id is not None else None, name.strip())
            )
        for item in value.values():
            collected.extend(_collect_coros_workout_names(item))
    elif isinstance(value, list):
        for item in value:
            collected.extend(_collect_coros_workout_names(item))
    return collected


def _find_coros_id(value: Any) -> str | None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"idInPlan", "id_in_plan"} and item is not None:
                return str(item)
            found = _find_coros_id(item)
            if found:
                return found
    elif isinstance(value, list):
        for item in value:
            found = _find_coros_id(item)
            if found:
                return found
    return None


@router.post("/sync")
def sync_coros_history(
    athlete_profile_id: UUID = Depends(get_current_athlete_profile_id),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Import synchrone compatible, exécuté par le worker COROS partagé."""
    connection = _connection(db, athlete_profile_id)
    if connection is None or not connection.enabled:
        raise HTTPException(status_code=409, detail="Connecte d'abord ton compte COROS.")
    if db.get(CorosSyncLock, athlete_profile_id) is not None:
        raise HTTPException(status_code=409, detail="Une synchronisation COROS est déjà en cours.")

    job = COROS_SYNC_JOBS.create(athlete_profile_id)
    job_id = job.id
    db.add(CorosSyncLock(
        athlete_profile_id=athlete_profile_id,
        job_id=str(job_id),
    ))
    connection.config = {
        **(connection.config or {}),
        "coros_sync_job": {
            "job_id": str(job_id),
            "worker_pid": os.getpid(),
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "finished_at": None,
            "result": None,
            "error": None,
            "progress": {"category": None, "next_date": None},
        },
    }
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        COROS_SYNC_JOBS.discard(job_id)
        raise HTTPException(
            status_code=409,
            detail="Une synchronisation COROS est déjà en cours.",
        ) from exc

    # Même worker que /sync/start : checkpoint, import initial, statut,
    # rafraîchissement OAuth et libération du verrou ont une seule implémentation.
    run_coros_sync_job(job_id=job_id, athlete_profile_id=athlete_profile_id)
    COROS_SYNC_JOBS.discard(job_id)

    db.expire_all()
    refreshed_connection = _connection(db, athlete_profile_id)
    state = (
        (refreshed_connection.config or {}).get("coros_sync_job")
        if refreshed_connection is not None
        else None
    )
    if not state or state.get("job_id") != str(job_id):
        raise HTTPException(
            status_code=500,
            detail="L'état de la synchronisation COROS est introuvable.",
        )
    if state.get("status") != "success":
        status_code = state.get("http_status", 502)
        if status_code not in {401, 502}:
            status_code = 502
        raise HTTPException(
            status_code=status_code,
            detail=state.get("error") or "La synchronisation COROS a échoué.",
        )
    return {"status": "completed", **(state.get("result") or {})}


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

    _recover_interrupted_coros_sync(db, athlete_profile_id, connection)
    existing_lock = db.get(CorosSyncLock, athlete_profile_id)
    if existing_lock is not None:
        persisted_job = (connection.config or {}).get("coros_sync_job") or {}
        # A live worker may legitimately run longer than the stale-lock
        # threshold. Never evict its lock just because a window is slow.
        if (
            persisted_job.get("job_id") == existing_lock.job_id
            and persisted_job.get("status") in {"pending", "running"}
        ):
            return {
                "job_id": existing_lock.job_id,
                "status": persisted_job["status"],
            }
        lock_age = datetime.now(timezone.utc).replace(tzinfo=None) - existing_lock.acquired_at
        if lock_age > timedelta(minutes=30):
            # Récupère un verrou orphelin après arrêt brutal du processus.
            db.delete(existing_lock)
            db.commit()
        else:
            return {"job_id": existing_lock.job_id, "status": "running"}

    job = COROS_SYNC_JOBS.create(athlete_profile_id)
    db.add(CorosSyncLock(
        athlete_profile_id=athlete_profile_id,
        job_id=str(job.id),
    ))
    try:
        connection.config = {
            **(connection.config or {}),
            "coros_sync_job": {
                "job_id": str(job.id),
                "worker_pid": os.getpid(),
                "status": "pending",
                "created_at": job.created_at.isoformat(),
                "finished_at": None,
                "result": None,
                "error": None,
                "progress": {"category": None, "next_date": None},
            },
        }
        db.commit()
    except IntegrityError:
        db.rollback()
        COROS_SYNC_JOBS.discard(job.id)
        existing_lock = db.get(CorosSyncLock, athlete_profile_id)
        if existing_lock is None:
            raise HTTPException(status_code=409, detail="Un import COROS est déjà en cours.")
        return {"job_id": existing_lock.job_id, "status": "running"}

    background_tasks.add_task(run_coros_sync_job, job_id=job.id, athlete_profile_id=athlete_profile_id)
    return {"job_id": str(job.id), "status": job.status}


@router.get("/sync/status/{job_id}")
def get_coros_sync_status(
    job_id: UUID,
    athlete_profile_id: UUID = Depends(get_current_athlete_profile_id),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    connection = _connection(db, athlete_profile_id)
    _recover_interrupted_coros_sync(db, athlete_profile_id, connection)
    state = (connection.config or {}).get("coros_sync_job") if connection else None
    if not state or state.get("job_id") != str(job_id):
        raise HTTPException(status_code=404, detail="Import COROS introuvable.")
    return {
        "job_id": state["job_id"],
        "status": state.get("status", "unknown"),
        "created_at": state.get("created_at"),
        "finished_at": state.get("finished_at"),
        "result": state.get("result"),
        "error": state.get("error"),
        "progress": state.get("progress"),
    }
