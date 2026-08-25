import os
import sqlite3
import subprocess
import sys
from pathlib import Path

from sqlalchemy import text

from opencoach.database.session import (
    DEFAULT_DATABASE_URL,
    _sqlite_connect_args,
    create_database_engine,
)


def test_default_database_url_uses_project_data_directory() -> None:
    assert DEFAULT_DATABASE_URL.endswith(
        "/data/opencoach.db"
    )


def test_sqlite_connect_args_enable_thread_sharing_and_timeout() -> None:
    args = _sqlite_connect_args(
        "sqlite:///:memory:"
    )

    assert args == {
        "check_same_thread": False,
        "timeout": 5.0,
    }


def test_sqlite_file_parent_directory_is_created(
    tmp_path: Path,
) -> None:
    database_path = (
        tmp_path
        / "nested"
        / "database"
        / "opencoach.db"
    )

    engine = create_database_engine(
        f"sqlite:///{database_path}"
    )

    try:
        with engine.connect():
            pass

        assert database_path.parent.is_dir()

    finally:
        engine.dispose()


def test_sqlite_foreign_keys_are_enabled() -> None:
    engine = create_database_engine(
        "sqlite:///:memory:"
    )

    try:
        with engine.connect() as connection:
            value = connection.execute(
                text(
                    "PRAGMA foreign_keys"
                )
            ).scalar_one()

        assert value == 1

    finally:
        engine.dispose()


def test_sqlite_busy_timeout_is_configured() -> None:
    engine = create_database_engine(
        "sqlite:///:memory:"
    )

    try:
        with engine.connect() as connection:
            value = connection.execute(
                text(
                    "PRAGMA busy_timeout"
                )
            ).scalar_one()

        assert value == 5000

    finally:
        engine.dispose()


def test_sqlite_file_uses_wal(
    tmp_path: Path,
) -> None:
    database_path = (
        tmp_path
        / "wal.db"
    )

    engine = create_database_engine(
        f"sqlite:///{database_path}"
    )

    try:
        with engine.connect() as connection:
            value = connection.execute(
                text(
                    "PRAGMA journal_mode"
                )
            ).scalar_one()

        assert value.lower() == "wal"

    finally:
        engine.dispose()


def test_sqlite_memory_database_does_not_require_wal() -> None:
    engine = create_database_engine(
        "sqlite:///:memory:"
    )

    try:
        with engine.connect() as connection:
            value = connection.execute(
                text(
                    "PRAGMA journal_mode"
                )
            ).scalar_one()

        assert value.lower() != "wal"

    finally:
        engine.dispose()


def test_database_url_can_be_overridden_by_environment(
    tmp_path: Path,
) -> None:
    database_path = (
        tmp_path
        / "custom.db"
    )

    database_url = (
        f"sqlite:///{database_path}"
    )

    env = os.environ.copy()

    env[
        "OPENCOACH_DATABASE_URL"
    ] = database_url

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from opencoach.database.session "
                "import DATABASE_URL; "
                "print(DATABASE_URL)"
            ),
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )

    assert (
        result.stdout.strip()
        == database_url
    )
