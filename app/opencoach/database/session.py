from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session, sessionmaker


PROJECT_ROOT = Path(__file__).resolve().parents[3]

DEFAULT_DATABASE_PATH = (
    PROJECT_ROOT
    / "data"
    / "opencoach.db"
)

DEFAULT_DATABASE_URL = (
    f"sqlite:///{DEFAULT_DATABASE_PATH}"
)

DATABASE_URL = os.getenv(
    "OPENCOACH_DATABASE_URL",
    DEFAULT_DATABASE_URL,
)


def _prepare_sqlite_storage(
    database_url: str,
) -> None:
    """Prépare le répertoire d'une base SQLite fichier."""

    url = make_url(
        database_url
    )

    if url.get_backend_name() != "sqlite":
        return

    database = url.database

    if not database:
        return

    if database == ":memory:":
        return

    path = Path(
        database
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )


def _sqlite_connect_args(
    database_url: str,
) -> dict[str, object]:
    """Retourne les options DBAPI spécifiques à SQLite."""

    url = make_url(
        database_url
    )

    if url.get_backend_name() != "sqlite":
        return {}

    return {
        "check_same_thread": False,
        "timeout": 5.0,
    }


def _configure_sqlite_connection(
    dbapi_connection: object,
    _connection_record: object,
) -> None:
    """Configure chaque connexion SQLite OpenCoach."""

    if not isinstance(
        dbapi_connection,
        sqlite3.Connection,
    ):
        return

    cursor = dbapi_connection.cursor()

    try:
        cursor.execute(
            "PRAGMA foreign_keys=ON"
        )

        cursor.execute(
            "PRAGMA busy_timeout=5000"
        )

        database_rows = cursor.execute(
            "PRAGMA database_list"
        ).fetchall()

        main_database = next(
            (
                row[2]
                for row in database_rows
                if row[1] == "main"
            ),
            "",
        )

        if (
            main_database
            and main_database != ":memory:"
        ):
            cursor.execute(
                "PRAGMA journal_mode=WAL"
            )

    finally:
        cursor.close()


def create_database_engine(
    database_url: str = DATABASE_URL,
) -> Engine:
    """Construit le moteur SQLAlchemy OpenCoach."""

    _prepare_sqlite_storage(
        database_url
    )

    engine = create_engine(
        database_url,
        connect_args=(
            _sqlite_connect_args(
                database_url
            )
        ),
    )

    if (
        make_url(database_url)
        .get_backend_name()
        == "sqlite"
    ):
        event.listen(
            engine,
            "connect",
            _configure_sqlite_connection,
        )

    return engine


engine = create_database_engine()

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def get_db() -> Session:
    """Fournit une session SQLAlchemy à l'appelant."""

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
