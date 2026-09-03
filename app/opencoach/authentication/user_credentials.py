"""Identifiants utilisateur OpenCoach."""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import unicodedata

from sqlalchemy import select
from sqlalchemy.orm import Session

from opencoach.database.models.user import User


PIN_LENGTH = 6


def normalize_identifier_part(
    value: str,
) -> str:
    normalized = unicodedata.normalize(
        "NFD",
        value,
    )

    without_accents = "".join(
        char
        for char in normalized
        if unicodedata.category(char)
        != "Mn"
    )

    return "".join(
        char.lower()
        for char in without_accents
        if char.isalpha()
    )


def generate_username(
    db: Session,
    *,
    first_name: str,
    last_name: str,
) -> str:
    first = normalize_identifier_part(
        first_name,
    )

    last = normalize_identifier_part(
        last_name,
    )

    if not first or not last:
        raise ValueError(
            "Prénom et nom requis."
        )

    prefix = (
        last[:2].ljust(
            2,
            "x",
        )
        + first[:1]
    )

    for _ in range(1000):
        suffix = (
            f"{secrets.randbelow(1000):03d}"
        )

        username = (
            prefix
            + suffix
        )

        existing = db.scalar(
            select(User.id)
            .where(
                User.username
                == username
            )
        )

        if existing is None:
            return username

    raise RuntimeError(
        "Impossible de générer "
        "un identifiant unique."
    )


def hash_pin(
    pin: str,
) -> tuple[str, str]:
    if (
        len(pin) != PIN_LENGTH
        or not pin.isdigit()
    ):
        raise ValueError(
            "Le PIN doit contenir "
            "exactement 6 chiffres."
        )

    salt = secrets.token_bytes(
        16,
    )

    digest = hashlib.scrypt(
        pin.encode(
            "utf-8",
        ),
        salt=salt,
        n=2**15,
        r=8,
        p=1,
        dklen=32,
        maxmem=64 * 1024 * 1024,
    )

    return (
        base64.urlsafe_b64encode(
            digest,
        ).decode(
            "ascii",
        ),
        base64.urlsafe_b64encode(
            salt,
        ).decode(
            "ascii",
        ),
    )


def verify_user_pin(
    pin: str,
    *,
    pin_hash: str,
    pin_salt: str,
) -> bool:
    if (
        len(pin) != PIN_LENGTH
        or not pin.isdigit()
    ):
        return False

    salt = base64.urlsafe_b64decode(
        pin_salt.encode(
            "ascii",
        )
    )

    expected = (
        base64.urlsafe_b64decode(
            pin_hash.encode(
                "ascii",
            )
        )
    )

    candidate = hashlib.scrypt(
        pin.encode(
            "utf-8",
        ),
        salt=salt,
        n=2**15,
        r=8,
        p=1,
        dklen=32,
        maxmem=64 * 1024 * 1024,
    )

    return hmac.compare_digest(
        candidate,
        expected,
    )
