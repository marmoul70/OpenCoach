"""Configuration du moteur IA local."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import ipaddress
import math
import os
import re
from urllib.parse import urlsplit

from opencoach.environment import load_environment


class AIConfigurationError(ValueError):
    """Configuration du moteur IA invalide."""


@dataclass(frozen=True, slots=True)
class AISettings:
    """Paramètres validés du fournisseur IA local."""

    enabled: bool = False
    provider: str = "ollama"
    base_url: str = "http://127.0.0.1:11434"
    model: str = "phi4-mini:latest"
    connect_timeout_seconds: float = 2.0
    read_timeout_seconds: float = 90.0
    max_concurrency: int = 1

    @classmethod
    def from_environment(cls) -> "AISettings":
        """Construit les paramètres depuis l'environnement OpenCoach."""
        load_environment()

        enabled = _read_bool("OPENCOACH_AI_ENABLED", False)
        provider = os.getenv("OPENCOACH_AI_PROVIDER", "ollama").strip().lower()
        base_url = os.getenv(
            "OPENCOACH_AI_BASE_URL",
            "http://127.0.0.1:11434",
        ).strip().rstrip("/")
        model = os.getenv(
            "OPENCOACH_AI_MODEL",
            "phi4-mini:latest",
        ).strip()
        connect_timeout = _read_float(
            "OPENCOACH_AI_CONNECT_TIMEOUT_SECONDS",
            2.0,
        )
        read_timeout = _read_float(
            "OPENCOACH_AI_READ_TIMEOUT_SECONDS",
            90.0,
        )
        max_concurrency = _read_int(
            "OPENCOACH_AI_MAX_CONCURRENCY",
            1,
        )

        if provider != "ollama":
            raise AIConfigurationError(
                "OPENCOACH_AI_PROVIDER doit être 'ollama'."
            )

        parsed_url = urlsplit(base_url)
        if (
            parsed_url.scheme not in {"http", "https"}
            or not parsed_url.netloc
            or parsed_url.username
            or parsed_url.password
            or parsed_url.query
            or parsed_url.fragment
            or not parsed_url.hostname
        ):
            raise AIConfigurationError(
                "OPENCOACH_AI_BASE_URL doit être une URL HTTP(S) valide sans identifiants."
            )

        try:
            # Accessing .port forces urllib to reject malformed/out-of-range ports.
            parsed_url.port
        except ValueError as exc:
            raise AIConfigurationError(
                "OPENCOACH_AI_BASE_URL contient un port invalide."
            ) from exc

        hostname = parsed_url.hostname.lower()
        try:
            is_loopback = ipaddress.ip_address(hostname).is_loopback
        except ValueError:
            is_loopback = hostname == "localhost"
        if not is_loopback:
            raise AIConfigurationError(
                "OPENCOACH_AI_BASE_URL doit pointer vers la machine locale (localhost ou loopback)."
            )

        if not model or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/-]*", model):
            raise AIConfigurationError(
                "OPENCOACH_AI_MODEL est vide ou contient des caractères invalides."
            )

        if (
            not math.isfinite(connect_timeout)
            or not math.isfinite(read_timeout)
            or connect_timeout <= 0
            or read_timeout <= 0
        ):
            raise AIConfigurationError(
                "Les délais IA doivent être strictement positifs."
            )

        if not 1 <= max_concurrency <= 8:
            raise AIConfigurationError(
                "OPENCOACH_AI_MAX_CONCURRENCY doit être compris entre 1 et 8."
            )

        return cls(
            enabled=enabled,
            provider=provider,
            base_url=base_url,
            model=model,
            connect_timeout_seconds=connect_timeout,
            read_timeout_seconds=read_timeout,
            max_concurrency=max_concurrency,
        )


def _read_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    normalized = raw.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise AIConfigurationError(f"{name} doit être un booléen.")


def _read_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise AIConfigurationError(f"{name} doit être un nombre.") from exc


def _read_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise AIConfigurationError(f"{name} doit être un entier.") from exc


@lru_cache(maxsize=1)
def get_ai_settings() -> AISettings:
    """Retourne la configuration IA mise en cache."""
    return AISettings.from_environment()


def clear_ai_settings_cache() -> None:
    """Vide le cache de configuration, notamment pour les tests."""
    get_ai_settings.cache_clear()
