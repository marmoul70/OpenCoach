"""Tests des protections de la base de données."""

from pathlib import Path

import pytest
import sqlalchemy


PROJECT_ROOT = Path(__file__).resolve().parents[1]

PRODUCTION_DATABASE_PATH = (
    PROJECT_ROOT
    / "data"
    / "opencoach.db"
).resolve()


def test_production_database_is_blocked() -> None:
    """La vraie base OpenCoach ne doit jamais être ouverte par pytest."""

    database_url = (
        f"sqlite:///{PRODUCTION_DATABASE_PATH}"
    )

    with pytest.raises(
        pytest.fail.Exception,
        match="Accès interdit à la base OpenCoach réelle",
    ):
        sqlalchemy.create_engine(
            database_url
        )


def test_memory_database_is_allowed() -> None:
    """Les bases SQLite en mémoire restent autorisées."""

    engine = sqlalchemy.create_engine(
        "sqlite:///:memory:"
    )

    try:
        with engine.connect() as connection:
            assert connection is not None
    finally:
        engine.dispose()
