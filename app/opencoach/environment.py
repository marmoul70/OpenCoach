"""Chargement centralisé de l'environnement OpenCoach."""

from __future__ import annotations

import os

from pathlib import Path


def project_root() -> Path:
    """Retourne la racine du projet OpenCoach."""
    return Path(__file__).resolve().parents[2]


def _parse_env_line(
    line: str,
) -> tuple[str, str] | None:
    """Analyse une ligne simple d'un fichier .env."""
    stripped = line.strip()

    if (
        not stripped
        or stripped.startswith("#")
    ):
        return None

    if stripped.startswith("export "):
        stripped = stripped[7:].lstrip()

    if "=" not in stripped:
        return None

    key, value = stripped.split("=", 1)

    key = key.strip()
    value = value.strip()

    if not key:
        return None

    if (
        len(value) >= 2
        and value[0] == value[-1]
        and value[0] in {"'", '"'}
    ):
        value = value[1:-1]

    return key, value


def load_environment(
    env_path: Path | None = None,
) -> None:
    """Charge le fichier .env OpenCoach.

    Les variables déjà définies dans l'environnement système
    restent prioritaires sur celles du fichier .env.

    L'absence du fichier .env n'est pas une erreur.
    """
    path = (
        env_path
        if env_path is not None
        else project_root() / ".env"
    )

    if not path.is_file():
        return

    content = path.read_text(
        encoding="utf-8",
    )

    for raw_line in content.splitlines():
        parsed = _parse_env_line(
            raw_line
        )

        if parsed is None:
            continue

        key, value = parsed

        os.environ.setdefault(
            key,
            value,
        )


load_environment()
