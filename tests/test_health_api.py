from __future__ import annotations

from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from opencoach.api.app import create_app
from opencoach.database.session import get_db


def test_health_reports_fastapi_liveness() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.get(
        "/api/health"
    )

    assert response.status_code == 200

    assert response.json() == {
        "status": "healthy",
    }


def test_readiness_reports_database_health() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.get(
        "/api/health/ready"
    )

    assert response.status_code == 200

    assert response.json() == {
        "status": "healthy",
        "database": "healthy",
    }


class _UnavailableDatabaseSession:
    def execute(
        self,
        _statement: object,
    ) -> None:
        raise OperationalError(
            statement="SELECT 1",
            params={},
            orig=RuntimeError(
                "database unavailable"
            ),
        )


def test_readiness_returns_503_when_database_is_unavailable(
) -> None:
    app = create_app()

    def unavailable_database(
    ) -> Generator[
        Session,
        None,
        None,
    ]:
        yield _UnavailableDatabaseSession()  # type: ignore[misc]

    app.dependency_overrides[
        get_db
    ] = unavailable_database

    client = TestClient(app)

    response = client.get(
        "/api/health/ready"
    )

    assert response.status_code == 503

    assert response.json() == {
        "status": "unhealthy",
        "database": "unhealthy",
    }
