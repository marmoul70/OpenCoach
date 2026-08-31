"""Authentification locale OpenCoach par PIN."""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
import time

from dataclasses import dataclass
from pathlib import Path


COOKIE_NAME = "opencoach_session"

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[3]
)

ENV_PATH = (
    PROJECT_ROOT
    / ".env"
)


def _load_local_env() -> dict[str, str]:
    values: dict[str, str] = {}

    if not ENV_PATH.exists():
        return values

    for raw_line in ENV_PATH.read_text(
        encoding="utf-8",
    ).splitlines():
        line = raw_line.strip()

        if (
            not line
            or line.startswith("#")
            or "=" not in line
        ):
            continue

        key, value = line.split(
            "=",
            1,
        )

        values[
            key.strip()
        ] = value.strip()

    return values


def _setting(
    name: str,
) -> str | None:
    environment_value = (
        os.environ.get(
            name
        )
    )

    if environment_value:
        return environment_value

    return (
        _load_local_env()
        .get(name)
    )


@dataclass(
    frozen=True,
    slots=True,
)
class AuthSettings:
    pin_salt: bytes
    pin_hash: bytes
    session_secret: bytes
    session_days: int
    max_attempts: int
    lock_seconds: int


def get_auth_settings() -> AuthSettings:
    salt_raw = _setting(
        "OPENCOACH_AUTH_PIN_SALT"
    )

    hash_raw = _setting(
        "OPENCOACH_AUTH_PIN_HASH"
    )

    secret_raw = _setting(
        "OPENCOACH_AUTH_SESSION_SECRET"
    )

    if (
        not salt_raw
        or not hash_raw
        or not secret_raw
    ):
        raise RuntimeError(
            "Authentification OpenCoach "
            "non configurée."
        )

    return AuthSettings(
        pin_salt=(
            base64
            .urlsafe_b64decode(
                salt_raw
            )
        ),
        pin_hash=(
            base64
            .urlsafe_b64decode(
                hash_raw
            )
        ),
        session_secret=(
            secret_raw.encode(
                "utf-8"
            )
        ),
        session_days=int(
            _setting(
                "OPENCOACH_AUTH_SESSION_DAYS"
            )
            or "30"
        ),
        max_attempts=int(
            _setting(
                "OPENCOACH_AUTH_MAX_ATTEMPTS"
            )
            or "5"
        ),
        lock_seconds=int(
            _setting(
                "OPENCOACH_AUTH_LOCK_SECONDS"
            )
            or "300"
        ),
    )


def verify_pin(
    pin: str,
) -> bool:
    if (
        len(pin) != 6
        or not pin.isdigit()
    ):
        return False

    settings = (
        get_auth_settings()
    )

    candidate = hashlib.scrypt(
        pin.encode(
            "utf-8"
        ),
        salt=settings.pin_salt,
        n=2**15,
        r=8,
        p=1,
        dklen=32,
    maxmem=64 * 1024 * 1024,
    )

    return hmac.compare_digest(
        candidate,
        settings.pin_hash,
    )


def create_session_token() -> tuple[
    str,
    int,
]:
    settings = (
        get_auth_settings()
    )

    max_age = (
        settings.session_days
        * 24
        * 60
        * 60
    )

    expires_at = (
        int(
            time.time()
        )
        + max_age
    )

    nonce = secrets.token_urlsafe(
        24
    )

    payload = (
        f"{expires_at}.{nonce}"
    )

    signature = hmac.new(
        settings.session_secret,
        payload.encode(
            "utf-8"
        ),
        hashlib.sha256,
    ).hexdigest()

    return (
        f"{payload}.{signature}",
        max_age,
    )


def verify_session_token(
    token: str | None,
) -> bool:
    if not token:
        return False

    try:
        expires_raw, nonce, signature = (
            token.split(
                ".",
                2,
            )
        )

        expires_at = int(
            expires_raw
        )

    except (
        TypeError,
        ValueError,
    ):
        return False

    if (
        expires_at
        <= int(
            time.time()
        )
    ):
        return False

    payload = (
        f"{expires_at}.{nonce}"
    )

    settings = (
        get_auth_settings()
    )

    expected = hmac.new(
        settings.session_secret,
        payload.encode(
            "utf-8"
        ),
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(
        signature,
        expected,
    )
