"""Configuration globale de la suite de tests OpenCoach.

Ce module contient les garde-fous communs à pytest.

La suite de tests ne doit jamais accéder à la base SQLite réelle
située dans ``data/opencoach.db``.
"""

from pathlib import Path

import pytest
import sqlalchemy


PROJECT_ROOT = Path(__file__).resolve().parents[1]

PRODUCTION_DATABASE_PATH = (
    PROJECT_ROOT
    / "data"
    / "opencoach.db"
).resolve()


@pytest.fixture(
    autouse=True,
)
def protect_production_database(
    monkeypatch: pytest.MonkeyPatch,
):
    """Interdit l'ouverture de la base réelle pendant les tests."""

    original_create_engine = sqlalchemy.create_engine

    def guarded_create_engine(
        url,
        *args,
        **kwargs,
    ):
        url_string = str(url)

        if url_string.startswith("sqlite:///"):
            database_path = url_string.removeprefix(
                "sqlite:///"
            )

            if database_path != ":memory:":
                resolved_path = Path(
                    database_path
                ).expanduser().resolve()

                if (
                    resolved_path
                    == PRODUCTION_DATABASE_PATH
                ):
                    pytest.fail(
                        (
                            "Accès interdit à la base OpenCoach "
                            "réelle pendant les tests : "
                            f"{PRODUCTION_DATABASE_PATH}"
                        ),
                        pytrace=False,
                    )

        return original_create_engine(
            url,
            *args,
            **kwargs,
        )

    monkeypatch.setattr(
        sqlalchemy,
        "create_engine",
        guarded_create_engine,
    )


@pytest.fixture(
    autouse=True,
)
def authenticate_api_tests(
    monkeypatch: pytest.MonkeyPatch,
    request: pytest.FixtureRequest,
):
    """Authentifie les requêtes API des tests fonctionnels.

    L'application protège les routes ``/api/*`` avec
    ``AuthenticationMiddleware``.

    Les tests métier ne testent pas l'authentification elle-même :
    ils doivent donc pouvoir atteindre directement leurs endpoints.

    Les tests dédiés à l'authentification peuvent demander le
    comportement réel avec le marqueur ``real_auth``.
    """

    if request.node.get_closest_marker(
        "real_auth"
    ) is not None:
        return

    monkeypatch.setattr(
        (
            "opencoach.authentication.middleware."
            "verify_session_token"
        ),
        lambda token: True,
    )
