"""Tests du chargement centralisé de l'environnement."""

from __future__ import annotations

import os

from pathlib import Path

from opencoach.environment import (
    _parse_env_line,
    load_environment,
)


def test_parse_basic_assignment() -> None:
    assert _parse_env_line(
        "SMTP_HOST=smtp.example.com"
    ) == (
        "SMTP_HOST",
        "smtp.example.com",
    )


def test_parse_value_containing_equals() -> None:
    assert _parse_env_line(
        "TOKEN=abc=def=="
    ) == (
        "TOKEN",
        "abc=def==",
    )


def test_parse_export_assignment() -> None:
    assert _parse_env_line(
        "export OPENCOACH_SECRET_KEY=secret"
    ) == (
        "OPENCOACH_SECRET_KEY",
        "secret",
    )


def test_parse_quoted_value() -> None:
    assert _parse_env_line(
        'SMTP_FROM_NAME="OpenCoach"'
    ) == (
        "SMTP_FROM_NAME",
        "OpenCoach",
    )


def test_parse_single_quoted_value() -> None:
    assert _parse_env_line(
        "SMTP_FROM_NAME='OpenCoach'"
    ) == (
        "SMTP_FROM_NAME",
        "OpenCoach",
    )


def test_ignore_comment() -> None:
    assert _parse_env_line(
        "# commentaire"
    ) is None


def test_ignore_empty_line() -> None:
    assert _parse_env_line(
        ""
    ) is None


def test_ignore_invalid_line() -> None:
    assert _parse_env_line(
        "INVALID"
    ) is None


def test_load_environment(
    tmp_path: Path,
    monkeypatch,
) -> None:
    variable = "OPENCOACH_ENV_TEST"

    monkeypatch.delenv(
        variable,
        raising=False,
    )

    env_file = tmp_path / ".env"

    env_file.write_text(
        f"{variable}=loaded\n",
        encoding="utf-8",
    )

    load_environment(
        env_file
    )

    assert (
        os.environ[variable]
        == "loaded"
    )


def test_existing_environment_has_priority(
    tmp_path: Path,
    monkeypatch,
) -> None:
    variable = "OPENCOACH_ENV_PRIORITY_TEST"

    monkeypatch.setenv(
        variable,
        "system-value",
    )

    env_file = tmp_path / ".env"

    env_file.write_text(
        f"{variable}=dotenv-value\n",
        encoding="utf-8",
    )

    load_environment(
        env_file
    )

    assert (
        os.environ[variable]
        == "system-value"
    )


def test_missing_env_file_is_allowed(
    tmp_path: Path,
) -> None:
    load_environment(
        tmp_path
        / "does-not-exist.env"
    )
