"""Routes d'authentification OpenCoach."""

from __future__ import annotations

import re
import time

from collections import defaultdict
from datetime import datetime, timezone
from uuid import UUID
from dataclasses import dataclass

from fastapi import (
    APIRouter,
    HTTPException,
    Request,
    Response,
)

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from sqlalchemy import select

from opencoach.database.models.athlete_profile import (
    AthleteProfile,
)
from opencoach.database.models.user import User
from opencoach.database.session import SessionLocal
from opencoach.authentication.user_credentials import (
    generate_username,
    hash_pin,
    verify_user_pin,
)

from opencoach.authentication import (
    COOKIE_NAME,
    create_session_token,
    get_auth_settings,
    verify_session_token,
)

from opencoach.email_service import (
    send_welcome_email_safely,
)


router = APIRouter(
    prefix="/api/auth",
    tags=[
        "authentication",
    ],
)


class RegisterRequest(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid"
    )

    first_name: str = Field(
        min_length=1,
        max_length=100,
    )

    last_name: str = Field(
        min_length=1,
        max_length=100,
    )

    email: str = Field(
        min_length=3,
        max_length=320,
    )

    pin: str = Field(
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
    )


class RegisterResponse(
    BaseModel
):
    username: str
    email: str


class LoginRequest(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid"
    )

    username: str = Field(
        min_length=3,
        max_length=32,
        pattern=r"^[A-Za-z0-9]+$",
    )

    pin: str = Field(
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
    )


class ChangePinRequest(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid"
    )

    current_pin: str = Field(
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
    )

    new_pin: str = Field(
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
    )


class ChangePinResponse(
    BaseModel
):
    changed: bool


class AccountResponse(
    BaseModel
):
    username: str
    email: str
    active: bool


class UpdateAccountRequest(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid"
    )

    email: str = Field(
        min_length=3,
        max_length=320,
    )


class SessionResponse(
    BaseModel
):
    authenticated: bool


@dataclass
class LoginState:
    failures: int = 0
    locked_until: float = 0


_login_states: dict[
    str,
    LoginState,
] = defaultdict(
    LoginState
)


def _client_key(
    request: Request,
) -> str:
    forwarded = request.headers.get(
        "cf-connecting-ip"
    )

    if forwarded:
        return forwarded

    if request.client:
        return request.client.host

    return "unknown"


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=201,
)
def register(
    payload: RegisterRequest,
) -> RegisterResponse:
    db = SessionLocal()

    try:
        email = (
            payload.email
            .strip()
            .lower()
        )

        if not re.fullmatch(
            r"[^\s@]+@[^\s@]+\.[^\s@]+",
            email,
        ):
            raise HTTPException(
                status_code=422,
                detail=(
                    "Adresse e-mail invalide."
                ),
            )

        existing_email = db.scalar(
            select(User.id)
            .where(
                User.email
                == email
            )
        )

        if existing_email is not None:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Cette adresse e-mail "
                    "est déjà utilisée."
                ),
            )

        username = generate_username(
            db,
            first_name=(
                payload.first_name
            ),
            last_name=(
                payload.last_name
            ),
        )

        pin_hash, pin_salt = (
            hash_pin(
                payload.pin,
            )
        )

        user = User(
            email=email,
            username=username,
            pin_hash=pin_hash,
            pin_salt=pin_salt,
            active=True,
        )

        profile = AthleteProfile(
            user=user,
            first_name=(
                payload.first_name
                .strip()
            ),
            last_name=(
                payload.last_name
                .strip()
            ),
        )

        db.add(
            profile,
        )

        db.commit()

        send_welcome_email_safely(
            recipient_email=email,
            first_name=(
                payload.first_name
                .strip()
            ),
            username=username,
        )

        return RegisterResponse(
            username=username,
            email=email,
        )

    except HTTPException:
        db.rollback()
        raise

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Impossible de créer "
                "le compte OpenCoach."
            ),
        ) from exc

    finally:
        db.close()


def _set_session_cookie(
    *,
    request: Request,
    response: Response,
    user_id: str | None,
) -> None:
    token, max_age = (
        create_session_token(
            user_id,
        )
    )

    host = (
        request.headers
        .get(
            "host",
            "",
        )
        .split(
            ":",
            1,
        )[0]
        .lower()
    )

    secure_cookie = host not in {
        "localhost",
        "127.0.0.1",
        "::1",
    }

    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=max_age,
        httponly=True,
        secure=secure_cookie,
        samesite="lax",
        path="/",
    )


@router.post(
    "/login",
    response_model=SessionResponse,
)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
) -> SessionResponse:
    """Connexion normale par identifiant OpenCoach + PIN."""

    settings = (
        get_auth_settings()
    )

    key = _client_key(
        request
    )

    state = (
        _login_states[key]
    )

    now = time.monotonic()

    if (
        state.locked_until
        > now
    ):
        remaining = max(
            1,
            int(
                state.locked_until
                - now
            ),
        )

        raise HTTPException(
            status_code=429,
            detail=(
                "Trop de tentatives. "
                f"Réessayez dans {remaining} s."
            ),
        )

    username = (
        payload.username
        .strip()
        .lower()
    )

    db = SessionLocal()

    try:
        user = db.scalar(
            select(User)
            .where(
                User.username
                == username
            )
        )

        valid_credentials = (
            user is not None
            and user.pin_hash is not None
            and user.pin_salt is not None
            and verify_user_pin(
                payload.pin,
                pin_hash=user.pin_hash,
                pin_salt=user.pin_salt,
            )
        )

        if not valid_credentials:
            state.failures += 1

            if (
                state.failures
                >= settings.max_attempts
            ):
                state.failures = 0
                state.locked_until = (
                    now
                    + settings.lock_seconds
                )

            raise HTTPException(
                status_code=401,
                detail=(
                    "Identifiant ou code PIN incorrect."
                ),
            )

        assert user is not None

        if not user.active:
            raise HTTPException(
                status_code=403,
                detail=(
                    "Ce compte OpenCoach est désactivé."
                ),
            )

        _login_states.pop(
            key,
            None,
        )

        user.last_login_at = (
            datetime.now(
                timezone.utc,
            )
        )

        db.commit()

        _set_session_cookie(
            request=request,
            response=response,
            user_id=str(
                user.id
            ),
        )

        return SessionResponse(
            authenticated=True
        )

    except HTTPException:
        db.rollback()
        raise

    finally:
        db.close()


@router.post(
    "/change-pin",
    response_model=ChangePinResponse,
)
def change_pin(
    payload: ChangePinRequest,
    request: Request,
) -> ChangePinResponse:
    """Modifie le PIN de l'utilisateur authentifié."""

    session_user_id = getattr(
        request.state,
        "user_id",
        None,
    )

    if not session_user_id:
        raise HTTPException(
            status_code=401,
            detail=(
                "Session utilisateur invalide."
            ),
        )

    try:
        user_id = UUID(
            session_user_id
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=401,
            detail=(
                "Session utilisateur invalide."
            ),
        ) from exc

    if (
        payload.current_pin
        == payload.new_pin
    ):
        raise HTTPException(
            status_code=422,
            detail=(
                "Le nouveau code PIN doit être "
                "différent de l'ancien."
            ),
        )

    db = SessionLocal()

    try:
        user = db.scalar(
            select(User)
            .where(
                User.id
                == user_id
            )
        )

        if user is None:
            raise HTTPException(
                status_code=404,
                detail=(
                    "Compte utilisateur introuvable."
                ),
            )

        if (
            user.pin_hash is None
            or user.pin_salt is None
        ):
            raise HTTPException(
                status_code=409,
                detail=(
                    "Le compte ne possède pas "
                    "de code PIN configuré."
                ),
            )

        if not verify_user_pin(
            payload.current_pin,
            pin_hash=user.pin_hash,
            pin_salt=user.pin_salt,
        ):
            raise HTTPException(
                status_code=401,
                detail=(
                    "Code PIN actuel incorrect."
                ),
            )

        pin_hash, pin_salt = hash_pin(
            payload.new_pin,
        )

        user.pin_hash = pin_hash
        user.pin_salt = pin_salt

        db.commit()

        return ChangePinResponse(
            changed=True,
        )

    except HTTPException:
        db.rollback()
        raise

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Impossible de modifier "
                "le code PIN."
            ),
        ) from exc

    finally:
        db.close()


def _get_authenticated_user(
    request: Request,
    db,
) -> User:
    session_user_id = getattr(
        request.state,
        "user_id",
        None,
    )

    if not session_user_id:
        raise HTTPException(
            status_code=401,
            detail=(
                "Session utilisateur invalide."
            ),
        )

    try:
        user_id = UUID(
            session_user_id
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=401,
            detail=(
                "Session utilisateur invalide."
            ),
        ) from exc

    user = db.scalar(
        select(User)
        .where(
            User.id
            == user_id
        )
    )

    if user is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Compte utilisateur introuvable."
            ),
        )

    return user


@router.get(
    "/account",
    response_model=AccountResponse,
)
def get_account(
    request: Request,
) -> AccountResponse:
    """Retourne les informations du compte connecté."""

    db = SessionLocal()

    try:
        user = _get_authenticated_user(
            request,
            db,
        )

        if not user.username:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Le compte ne possède pas "
                    "d'identifiant OpenCoach."
                ),
            )

        return AccountResponse(
            username=user.username,
            email=user.email,
            active=user.active,
        )

    finally:
        db.close()


@router.patch(
    "/account",
    response_model=AccountResponse,
)
def update_account(
    payload: UpdateAccountRequest,
    request: Request,
) -> AccountResponse:
    """Modifie les informations éditables du compte."""

    email = (
        payload.email
        .strip()
        .lower()
    )

    if not re.fullmatch(
        r"[^\s@]+@[^\s@]+\.[^\s@]+",
        email,
    ):
        raise HTTPException(
            status_code=422,
            detail=(
                "Adresse e-mail invalide."
            ),
        )

    db = SessionLocal()

    try:
        user = _get_authenticated_user(
            request,
            db,
        )

        existing = db.scalar(
            select(User.id)
            .where(
                User.email
                == email,
                User.id
                != user.id,
            )
        )

        if existing is not None:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Cette adresse e-mail "
                    "est déjà utilisée."
                ),
            )

        user.email = email

        db.commit()
        db.refresh(
            user,
        )

        if not user.username:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Le compte ne possède pas "
                    "d'identifiant OpenCoach."
                ),
            )

        return AccountResponse(
            username=user.username,
            email=user.email,
            active=user.active,
        )

    except HTTPException:
        db.rollback()
        raise

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Impossible de modifier "
                "le compte OpenCoach."
            ),
        ) from exc

    finally:
        db.close()


@router.get(
    "/session",
    response_model=SessionResponse,
)
def session(
    request: Request,
) -> SessionResponse:
    authenticated = (
        verify_session_token(
            request.cookies.get(
                COOKIE_NAME
            )
        )
    )

    if not authenticated:
        raise HTTPException(
            status_code=401,
            detail=(
                "Authentification requise."
            ),
        )

    return SessionResponse(
        authenticated=True
    )


@router.post(
    "/logout",
    response_model=SessionResponse,
)
def logout(
    response: Response,
) -> SessionResponse:
    response.delete_cookie(
        COOKIE_NAME,
        path="/",
        httponly=True,
        samesite="lax",
    )

    return SessionResponse(
        authenticated=False
    )
