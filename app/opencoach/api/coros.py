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


def _reload_coros_training_session(
    db: Session,
    repository: SqlTrainingSessionRepository,
    athlete_profile_id: UUID,
    session_id: UUID,
):
    """Relit une séance après un appel externe sans réécrire un état périmé."""
    expire_all = getattr(db, "expire_all", None)
    if callable(expire_all):
        expire_all()
    return repository.get_session(athlete_profile_id, session_id)


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
    """Crée ou actualise la séance OpenCoach planifiée dans le calendrier COROS."""
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
    previous_payload_hash = training_session.coros_payload_hash
    is_update = False
    if current_status == "synced":
        if training_session.coros_payload_hash == workout_payload.payload_hash:
            return {
                "status": "synced",
                "last_synced_at": (
                    training_session.coros_last_synced_at.isoformat()
                    if training_session.coros_last_synced_at
                    else None
                ),
                "message": "Cette séance est déjà à jour dans ton calendrier COROS.",
            }
        if not training_session.coros_workout_id:
            raise HTTPException(
                status_code=409,
                detail=(
                    "La séance est marquée comme synchronisée mais son identifiant COROS "
                    "est absent. Aucune nouvelle séance ne sera créée par sécurité."
                ),
            )
        is_update = True
    elif current_status in {"unknown", "pending", "failed"}:
        # Un échec de mise à jour conserve l'identifiant COROS : la reprise
        # doit actualiser cette séance, jamais en créer une seconde.
        is_update = bool(training_session.coros_workout_id)

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
        # Pour un envoi ancien, on autorise d'abord la recherche de réconciliation.
        # La confirmation ne sera exigée que si aucune séance existante n'est retrouvée.

    if (
        is_update
        and current_status in {"unknown", "pending"}
        and (current_status == "unknown" or stale_pending)
        and not payload.confirmed_no_duplicate
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                "Le résultat de la précédente mise à jour COROS est incertain. "
                "Confirme la vérification du calendrier avant de réessayer."
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

    # Une création peut être acceptée par COROS alors que la réponse MCP
    # est perdue (par exemple HTTP 502 après effet de bord). Avant toute
    # nouvelle création depuis un état incertain, rechercher le titre exact
    # dans le calendrier et récupérer son idInPlan pour reprendre en UPDATE.
    recovery_schedule_checked = False
    existing_workouts: list[str] = []
    if (
        not is_update
        and current_status in {"unknown", "pending"}
    ):
        schedule_tool = next(
            (
                tool for tool in tools
                if tool.get("name") == "queryTrainingSchedule"
            ),
            None,
        )
        schedule_schema = (
            schedule_tool.get("inputSchema")
            if isinstance(schedule_tool, dict)
            else None
        )
        schedule_properties = (
            schedule_schema.get("properties", {})
            if isinstance(schedule_schema, dict)
            else {}
        )
        # COROS MCP's current queryTrainingSchedule schema uses startDate/endDate.
        # Keep the older startDay/endDay spellings as compatibility fallbacks for
        # regional or older deployments, and honor integer schemas if advertised.
        start_key = next(
            (
                key for key in (
                    "startDate", "startDay", "start_date", "start_day",
                )
                if key in schedule_properties
            ),
            None,
        )
        end_key = next(
            (
                key for key in (
                    "endDate", "endDay", "end_date", "end_day",
                )
                if key in schedule_properties
            ),
            None,
        )
        if start_key and end_key:
            schedule_day = training_session.date.strftime("%Y%m%d")
            start_type = (
                schedule_properties.get(start_key, {}).get("type")
                if isinstance(schedule_properties.get(start_key), dict)
                else None
            )
            end_type = (
                schedule_properties.get(end_key, {}).get("type")
                if isinstance(schedule_properties.get(end_key), dict)
                else None
            )
            start_value = int(schedule_day) if start_type == "integer" else schedule_day
            end_value = int(schedule_day) if end_type == "integer" else schedule_day
            try:
                recovery_schedule = client.call_tool(
                    "queryTrainingSchedule",
                    {start_key: start_value, end_key: end_value},
                )
                recovery_schedule_checked = True
                existing_workouts = _extract_scheduled_workouts_for_date(
                    recovery_schedule,
                    training_session.date,
                )
            except CorosMcpAuthenticationError as exc:
                raise HTTPException(
                    status_code=401,
                    detail="La connexion COROS a expiré. Reconnecte ton compte.",
                ) from exc
            except CorosMcpError as exc:
                raise HTTPException(
                    status_code=502,
                    detail=(
                        "Impossible de vérifier le calendrier COROS pour "
                        "récupérer une création précédente. Aucun nouvel envoi "
                        "n'a été effectué."
                    ),
                ) from exc

            current_title = training_session.title.strip().casefold()
            matching = [
                (workout_id, name)
                for workout_id, name in _extract_scheduled_workout_records_for_date(
                    recovery_schedule,
                    training_session.date,
                )
                if name.strip().casefold() == current_title
            ]
            matching_ids = {
                workout_id for workout_id, _ in matching
                if workout_id
            }
            if len(matching_ids) == 1:
                training_session.coros_workout_id = next(iter(matching_ids))
                training_session.coros_scheduled_date = training_session.date
                repository.save_session(athlete_profile_id, training_session)
                is_update = True
            elif matching:
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "Une séance portant ce titre existe déjà dans COROS, "
                        "mais son identifiant ne peut pas être déterminé sans "
                        "ambiguïté. Aucun nouvel envoi n'a été effectué."
                    ),
                )

    if is_update:
        required_tools = {
            "queryScheduledWorkoutDetails": {"date", "idInPlan"},
            "updateScheduledWorkout": {"date", "idInPlan", "course"},
        }
    else:
        required_tools = {"createScheduledWorkout": {"date", "course"}}

    available_tools = {
        tool.get("name"): tool
        for tool in tools
        if isinstance(tool, dict) and tool.get("name")
    }
    for tool_name, required_arguments in required_tools.items():
        tool = available_tools.get(tool_name)
        if tool is None:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"La connexion COROS ne propose pas l'outil {tool_name}. "
                    "Aucune nouvelle séance ne sera créée en remplacement."
                ),
            )
        schema = tool.get("inputSchema")
        properties = (
            schema.get("properties")
            if isinstance(schema, dict)
            else None
        )
        required = (
            schema.get("required")
            if isinstance(schema, dict)
            else None
        )
        if (
            not isinstance(properties, dict)
            or not isinstance(required, list)
            or not all(isinstance(key, str) for key in required)
            or not required_arguments.issubset(required)
        ):
            raise HTTPException(
                status_code=502,
                detail=f"Le schéma COROS de {tool_name} est incomplet ou incompatible avec OpenCoach.",
            )

        expected_types = {
            "date": "string",
            "idInPlan": "string",
            "course": "object",
        }
        incompatible = [
            key
            for key in required_arguments
            if (
                not isinstance(properties.get(key), dict)
                or properties[key].get("type") != expected_types[key]
            )
        ]
        if incompatible:
            raise HTTPException(
                status_code=502,
                detail=(
                    f"Le schéma COROS de {tool_name} définit des types "
                    "d'arguments incompatibles avec OpenCoach."
                ),
            )

    if is_update:
        coros_existing_date = (
            training_session.coros_scheduled_date
            or training_session.date
        )
        lookup_dates = [coros_existing_date]
        if training_session.date != coros_existing_date:
            lookup_dates.append(training_session.date)

        details = None
        for lookup_index, lookup_date in enumerate(lookup_dates):
            try:
                details_result = client.call_tool(
                    "queryScheduledWorkoutDetails",
                    {
                        "date": lookup_date.strftime("%Y%m%d"),
                        "idInPlan": training_session.coros_workout_id,
                    },
                )
            except CorosMcpAuthenticationError as exc:
                raise HTTPException(
                    status_code=401,
                    detail="La connexion COROS a expiré. Reconnecte ton compte.",
                ) from exc
            except CorosMcpToolError as exc:
                # COROS peut signaler « introuvable » comme erreur outil
                # lorsque la séance a déjà été déplacée par une requête dont
                # la réponse a été perdue. Essayer alors la date cible connue.
                if lookup_index < len(lookup_dates) - 1:
                    continue
                raise HTTPException(
                    status_code=502,
                    detail=(
                        "Impossible de retrouver la séance COROS aux dates "
                        "connues. Aucune modification n'a été effectuée."
                    ),
                ) from exc
            except CorosMcpError as exc:
                raise HTTPException(
                    status_code=502,
                    detail=(
                        "Impossible de vérifier la séance déjà planifiée dans COROS. "
                        "Aucune modification n'a été effectuée."
                    ),
                ) from exc

            details = _extract_coros_scheduled_details(details_result)
            if details is not None:
                break

        if details is None:
            raise HTTPException(
                status_code=502,
                detail=(
                    "COROS n'a pas retourné un détail exploitable de la séance. "
                    "Aucune modification n'a été effectuée."
                ),
            )
        if details["editable"] is not True:
            reason = details.get("reason") or (
                "COROS indique que cette séance n'est pas modifiable."
            )
            raise HTTPException(status_code=409, detail=reason)
        existing_course = details.get("course")
        if not isinstance(existing_course, dict):
            raise HTTPException(
                status_code=502,
                detail=(
                    "COROS n'a pas retourné le contenu de la séance à remplacer. "
                    "Aucune modification n'a été effectuée."
                ),
            )
        # COROS impose un remplacement intégral. On part de la copie réellement
        # planifiée puis on remplace les champs maîtrisés par la prescription OpenCoach.
        replacement_course = dict(existing_course)
        replacement_course.update(workout_payload.course)
        replacement_course.pop("dayNo", None)
        replacement_course.pop("strengthBodypart", None)

    schedule_tool = next(
        (
            tool for tool in tools
            if tool.get("name") == "queryTrainingSchedule"
        ),
        None,
    )
    if (
        not is_update
        and schedule_tool is not None
        and not recovery_schedule_checked
    ):
        schedule_schema = schedule_tool.get("inputSchema")
        schedule_properties = (
            schedule_schema.get("properties", {})
            if isinstance(schedule_schema, dict)
            else {}
        )
        start_key = next(
            (
                key for key in ("startDay", "start_day")
                if key in schedule_properties
            ),
            None,
        )
        end_key = next(
            (
                key for key in ("endDay", "end_day")
                if key in schedule_properties
            ),
            None,
        )
        if start_key and end_key:
            schedule_day = training_session.date.strftime("%Y%m%d")
            try:
                schedule_result = client.call_tool(
                    "queryTrainingSchedule",
                    {
                        start_key: schedule_day,
                        end_key: schedule_day,
                    },
                )
            except CorosMcpAuthenticationError as exc:
                raise HTTPException(
                    status_code=401,
                    detail="La connexion COROS a expiré. Reconnecte ton compte.",
                ) from exc
            except CorosMcpError as exc:
                raise HTTPException(
                    status_code=502,
                    detail=(
                        "Impossible de vérifier le calendrier COROS avant l'ajout. "
                        "Aucune séance n'a été envoyée."
                    ),
                ) from exc
            existing_workouts = _extract_scheduled_workouts_for_date(
                schedule_result,
                training_session.date,
            )

    if current_status in {"pending", "unknown"} and not is_update:
        current_title = training_session.title.strip().casefold()
        matching_workouts = [
            name for name in existing_workouts
            if name.strip().casefold() == current_title
        ]
        if matching_workouts:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Une séance portant déjà ce titre est présente dans le "
                    "calendrier COROS, mais son identifiant n'a pas pu être "
                    "récupéré. Aucun nouvel envoi n'a été effectué."
                ),
            )

    if (
        current_status in {"unknown", "pending"}
        and not is_update
    ):
        # Une tentative précédente a pu créer la séance malgré une réponse
        # MCP perdue ou incomplète. Une confirmation utilisateur ne prouve
        # pas l'absence distante : ne jamais retomber sur CREATE dans cet état.
        # Seule la récupération d'un idInPlan permet de reprendre en UPDATE.
        raise HTTPException(
            status_code=409,
            detail=(
                "Le résultat d'un précédent envoi COROS reste incertain et "
                "aucun identifiant de séance existante n'a pu être récupéré. "
                "Par sécurité, OpenCoach bloque toute nouvelle création pour "
                "éviter un doublon. Vérifie le calendrier COROS ou contacte "
                "l'assistance avant toute autre action."
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
        allow_uncertain=(payload.confirmed_no_duplicate or is_update),
        allow_synced_update=is_update,
    )
    if not claimed:
        raise HTTPException(
            status_code=409,
            detail=(
                "Une autre requête a déjà réservé l'envoi de cette séance. "
                "Actualise la page avant de réessayer."
            ),
        )
    training_session = _reload_coros_training_session(
        db,
        repository,
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

    # Vérifier que la prescription n'a pas changé entre sa lecture initiale
    # et la réservation atomique. Le payload préparé doit encore représenter
    # exactement la séance qui va être envoyée.
    try:
        claimed_payload = map_training_session_to_coros(training_session)
    except CorosWorkoutMappingError as exc:
        training_session.coros_sync_status = "failed"
        training_session.coros_sync_started_at = None
        training_session.coros_sync_error = (
            "La séance a changé pendant la préparation de l'envoi. "
            "Corrige ou actualise la séance avant de réessayer."
        )
        repository.save_session(athlete_profile_id, training_session)
        raise HTTPException(
            status_code=409,
            detail=training_session.coros_sync_error,
        ) from exc

    if claimed_payload.payload_hash != workout_payload.payload_hash:
        training_session.coros_sync_status = "failed"
        training_session.coros_sync_started_at = None
        training_session.coros_sync_error = (
            "La séance OpenCoach a été modifiée pendant la préparation. "
            "Aucun contenu n'a été envoyé à COROS ; relance l'envoi."
        )
        repository.save_session(athlete_profile_id, training_session)
        raise HTTPException(status_code=409, detail=training_session.coros_sync_error)

    try:
        if is_update:
            result = client.call_tool(
                "updateScheduledWorkout",
                {
                    "date": workout_payload.date,
                    "idInPlan": training_session.coros_workout_id,
                    "course": replacement_course,
                },
            )
        else:
            result = client.call_tool(
                "createScheduledWorkout",
                workout_payload.as_tool_arguments(),
            )
    except CorosMcpAuthenticationError as exc:
        training_session = _reload_coros_training_session(
            db,
            repository,
            athlete_profile_id,
            session_id,
        )
        if training_session is None:
            raise HTTPException(
                status_code=404,
                detail="Séance introuvable après l'appel COROS.",
            )
        training_session.coros_sync_status = "synced" if is_update else "failed"
        training_session.coros_sync_started_at = None
        if is_update:
            training_session.coros_payload_hash = previous_payload_hash
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
        training_session = _reload_coros_training_session(
            db,
            repository,
            athlete_profile_id,
            session_id,
        )
        if training_session is None:
            raise HTTPException(status_code=404, detail="Séance introuvable après l'appel COROS.")
        training_session.coros_sync_status = "synced" if is_update else "failed"
        training_session.coros_sync_started_at = None
        if is_update:
            training_session.coros_payload_hash = previous_payload_hash
        training_session.coros_sync_error = str(exc)[:2000]
        repository.save_session(athlete_profile_id, training_session)
        raise HTTPException(
            status_code=422,
            detail=training_session.coros_sync_error,
        ) from exc
    except CorosMcpProtocolError as exc:
        training_session = _reload_coros_training_session(
            db,
            repository,
            athlete_profile_id,
            session_id,
        )
        if training_session is None:
            raise HTTPException(status_code=404, detail="Séance introuvable après l'appel COROS.")
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
        training_session = _reload_coros_training_session(
            db,
            repository,
            athlete_profile_id,
            session_id,
        )
        if training_session is None:
            raise HTTPException(status_code=404, detail="Séance introuvable après l'appel COROS.")
        training_session.coros_sync_status = "unknown"
        training_session.coros_sync_started_at = None
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
    returned_workout_id = _extract_coros_scheduled_id(result)
    if not is_update and not returned_workout_id:
        training_session = _reload_coros_training_session(
            db,
            repository,
            athlete_profile_id,
            session_id,
        )
        if training_session is None:
            raise HTTPException(status_code=404, detail="Séance introuvable après l'appel COROS.")
        # La création peut avoir réussi côté COROS, mais sans idInPlan
        # OpenCoach ne peut ni prouver la synchronisation ni mettre à jour
        # cette séance ensuite. Conserver un état incertain impose une
        # vérification du calendrier avant toute nouvelle création.
        training_session.coros_sync_status = "unknown"
        training_session.coros_sync_started_at = None
        training_session.coros_sync_error = (
            "COROS n'a pas retourné l'identifiant de la séance créée. "
            "Vérifie le calendrier COROS avant toute nouvelle tentative."
        )
        repository.save_session(athlete_profile_id, training_session)
        raise HTTPException(
            status_code=502,
            detail=training_session.coros_sync_error,
        )

    # Relire la séance après l'appel distant : une modification OpenCoach
    # pendant l'attente ne doit pas être présentée comme déjà synchronisée.
    latest_session = _reload_coros_training_session(
        db,
        repository,
        athlete_profile_id,
        session_id,
    )
    if latest_session is None:
        raise HTTPException(
            status_code=404,
            detail="Séance introuvable après l'envoi COROS.",
        )
    latest_session.coros_workout_id = (
        returned_workout_id
        or latest_session.coros_workout_id
    )
    latest_session.coros_scheduled_date = datetime.strptime(
        workout_payload.date,
        "%Y%m%d",
    ).date()
    try:
        latest_payload = map_training_session_to_coros(latest_session)
    except CorosWorkoutMappingError:
        latest_payload = None

    if (
        latest_payload is None
        or latest_payload.payload_hash != workout_payload.payload_hash
    ):
        latest_session.coros_sync_status = "failed"
        latest_session.coros_sync_started_at = None
        latest_session.coros_payload_hash = workout_payload.payload_hash
        latest_session.coros_sync_error = (
            "La séance OpenCoach a été modifiée pendant l'envoi. "
            "COROS a reçu la version précédente ; relance l'envoi pour "
            "mettre à jour la séance existante."
        )
        repository.save_session(athlete_profile_id, latest_session)
        raise HTTPException(
            status_code=409,
            detail=latest_session.coros_sync_error,
        )

    training_session = latest_session
    training_session.coros_sync_status = "synced"
    training_session.coros_sync_started_at = None
    training_session.coros_last_synced_at = now
    training_session.coros_sync_error = None
    saved_session = repository.save_session(
        athlete_profile_id,
        training_session,
    )
    other_workouts = list(dict.fromkeys([
        *existing_workouts,
        *_extract_other_coros_workouts(
            result,
            created_id=saved_session.coros_workout_id,
            current_name=saved_session.title,
        ),
    ]))
    action = "a été mise à jour" if is_update else "a été ajoutée"
    message = (
        f"« {saved_session.title} » {action} au calendrier COROS "
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


def _extract_coros_scheduled_details(
    result: dict[str, Any],
) -> dict[str, Any] | None:
    """Extrait l'état d'éditabilité d'une séance standalone COROS."""
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
            start = raw_text.find("{")
            end = raw_text.rfind("}")
            if start >= 0 and end > start:
                try:
                    candidates.append(json.loads(raw_text[start:end + 1]))
                except ValueError:
                    pass

    def find_course(value: Any) -> dict[str, Any] | None:
        if isinstance(value, dict):
            course = value.get("course")
            if isinstance(course, dict):
                return course
            if "courseName" in value and isinstance(value.get("sections"), list):
                return value
            for child in value.values():
                found = find_course(child)
                if found is not None:
                    return found
        elif isinstance(value, list):
            for child in value:
                found = find_course(child)
                if found is not None:
                    return found
        return None

    def find_editability(value: Any) -> tuple[bool, str | None] | None:
        if isinstance(value, dict):
            editable = value.get("editable")
            if isinstance(editable, bool):
                reason = value.get("reason") or value.get("reasons") or value.get("message")
                normalized_reason = (
                    "; ".join(str(item) for item in reason)
                    if isinstance(reason, list)
                    else str(reason) if reason else None
                )
                return editable, normalized_reason
            for child in value.values():
                found = find_editability(child)
                if found is not None:
                    return found
        elif isinstance(value, list):
            for child in value:
                found = find_editability(child)
                if found is not None:
                    return found
        return None

    for candidate in candidates:
        editability = find_editability(candidate)
        if editability is not None:
            editable, reason = editability
            return {
                "editable": editable,
                "reason": reason,
                "course": find_course(candidate),
            }
    return None


def _extract_scheduled_workout_records_for_date(
    result: dict[str, Any],
    target_date,
) -> list[tuple[str | None, str]]:
    """Extrait les identifiants et titres des séances planifiées à une date."""
    # All incoming COROS date representations are normalized by removing
    # hyphens before comparison, so keep the target in the same YYYYMMDD form.
    target_values = {
        target_date.strftime("%Y%m%d"),
        target_date.strftime("%Y-%m-%d"),
    }
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
                    candidates.append(json.loads(raw_text[object_start:object_end + 1]))
                except ValueError:
                    pass

    date_keys = {
        "date", "day", "happenDay", "happen_day",
        "scheduleDate", "schedule_date",
    }
    workout_list_keys = {
        "courses", "workouts", "entities", "programs",
        "scheduledWorkouts", "scheduled_workouts", "items",
    }
    found: list[tuple[str | None, str]] = []

    def collect(value: Any, *, in_workout_list: bool = False) -> None:
        if isinstance(value, dict):
            is_workout = in_workout_list or any(
                key in value
                for key in ("courseName", "workoutName", "idInPlan", "id_in_plan")
            )
            if is_workout:
                name = (
                    value.get("courseName")
                    or value.get("workoutName")
                    or value.get("name")
                    or value.get("title")
                )
                raw_id = value.get("idInPlan", value.get("id_in_plan"))
                if isinstance(name, str) and name.strip():
                    record = (
                        str(raw_id) if raw_id is not None else None,
                        name.strip(),
                    )
                    if record not in found:
                        found.append(record)
            for key, child in value.items():
                collect(child, in_workout_list=key in workout_list_keys)
        elif isinstance(value, list):
            for child in value:
                collect(child, in_workout_list=in_workout_list)

    def visit(value: Any, *, date_matches: bool = False) -> None:
        if isinstance(value, dict):
            matches_date = date_matches or any(
                str(value.get(key, "")).replace("-", "")[:8] in target_values
                for key in date_keys
                if value.get(key) is not None
            )
            if matches_date:
                for key, child in value.items():
                    if key in workout_list_keys:
                        collect(child, in_workout_list=True)
                if not any(key in value for key in workout_list_keys):
                    for child in value.values():
                        visit(child, date_matches=True)
                return
            for key, child in value.items():
                if str(key).replace("-", "")[:8] == target_date.strftime("%Y%m%d"):
                    collect(child, in_workout_list=True)
                else:
                    visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child, date_matches=date_matches)

    for candidate in candidates:
        visit(candidate)
    return found


def _extract_scheduled_workouts_for_date(
    result: dict[str, Any],
    target_date,
) -> list[str]:
    """Extrait les séances déjà planifiées à la date interrogée."""
    # All incoming COROS date representations are normalized by removing
    # hyphens before comparison, so keep the target in the same YYYYMMDD form.
    target_values = {target_date.strftime("%Y%m%d")}
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

    found: list[str] = []
    date_keys = {
        "date",
        "day",
        "happenDay",
        "happen_day",
        "scheduleDate",
        "schedule_date",
    }
    workout_list_keys = {
        "courses",
        "workouts",
        "entities",
        "programs",
        "scheduledWorkouts",
        "scheduled_workouts",
        "items",
    }

    def collect_workout_names(value: Any, *, in_workout_list: bool = False) -> None:
        if isinstance(value, dict):
            is_workout = in_workout_list or any(
                key in value
                for key in ("courseName", "workoutName", "idInPlan", "id_in_plan")
            )
            if is_workout:
                name = (
                    value.get("courseName")
                    or value.get("workoutName")
                    or value.get("name")
                    or value.get("title")
                )
                if isinstance(name, str) and name.strip() and name.strip() not in found:
                    found.append(name.strip())
            for key, child in value.items():
                collect_workout_names(
                    child,
                    in_workout_list=key in workout_list_keys,
                )
        elif isinstance(value, list):
            for child in value:
                collect_workout_names(child, in_workout_list=in_workout_list)

    def visit(value: Any, *, date_matches: bool = False) -> None:
        if isinstance(value, dict):
            matches = date_matches
            for key in date_keys:
                candidate_date = value.get(key)
                if candidate_date is not None:
                    normalized = str(candidate_date).replace("-", "")[:8]
                    if normalized in target_values:
                        matches = True
                        break
            if matches:
                for key, child in value.items():
                    if key in workout_list_keys:
                        collect_workout_names(child, in_workout_list=True)
                if not any(key in value for key in workout_list_keys):
                    for child in value.values():
                        visit(child, date_matches=True)
                return
            for key, child in value.items():
                if key in target_values:
                    collect_workout_names(child, in_workout_list=True)
                else:
                    visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child, date_matches=date_matches)

    for candidate in candidates:
        visit(candidate)
    return found


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
