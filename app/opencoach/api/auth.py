"""Routes d'authentification OpenCoach."""

from __future__ import annotations

import time

from collections import defaultdict
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

from opencoach.authentication import (
    COOKIE_NAME,
    create_session_token,
    get_auth_settings,
    verify_pin,
    verify_session_token,
)


router = APIRouter(
    prefix="/api/auth",
    tags=[
        "authentication",
    ],
)


class LoginRequest(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid"
    )

    pin: str = Field(
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
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
    "/login",
    response_model=SessionResponse,
)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
) -> SessionResponse:
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

    if not verify_pin(
        payload.pin
    ):
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
                "Code PIN incorrect."
            ),
        )

    _login_states.pop(
        key,
        None,
    )

    token, max_age = (
        create_session_token()
    )

    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=max_age,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
    )

    return SessionResponse(
        authenticated=True
    )


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
        secure=True,
        httponly=True,
        samesite="lax",
    )

    return SessionResponse(
        authenticated=False
    )
