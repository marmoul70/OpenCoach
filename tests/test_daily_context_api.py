from datetime import date
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from opencoach.api.app import create_app
from opencoach.api.daily_context import (
    get_daily_context_repository,
)
from opencoach.api.intervals import (
    get_local_athlete_profile_id,
)
from opencoach.models import DailyContext


PROFILE_ID = uuid4()


class FakeDailyContextRepository:
    def __init__(
        self,
        context: DailyContext | None = None,
    ) -> None:
        self.context = context

    def get_by_date(
        self,
        athlete_profile_id: UUID,
        context_date: date,
    ) -> DailyContext | None:
        if athlete_profile_id != PROFILE_ID:
            return None

        if self.context is None:
            return None

        if self.context.date != context_date:
            return None

        return self.context

    def save(
        self,
        athlete_profile_id: UUID,
        context: DailyContext,
    ) -> DailyContext:
        assert athlete_profile_id == PROFILE_ID

        self.context = context

        return context


def create_client(
    repository: FakeDailyContextRepository,
) -> TestClient:
    app = create_app()

    app.dependency_overrides[
        get_local_athlete_profile_id
    ] = lambda: PROFILE_ID

    app.dependency_overrides[
        get_daily_context_repository
    ] = lambda: repository

    return TestClient(app)


def test_daily_context_api_returns_today() -> None:
    repository = FakeDailyContextRepository(
        DailyContext(
            date=date.today(),
            fatigue_subjective=2,
            pain_level=1,
            illness_status="none",
            treatment_impact="none",
            motivation=4,
            notes="Bonne récupération.",
        )
    )

    client = create_client(
        repository
    )

    response = client.get(
        "/api/daily-context/today"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["date"] == (
        date.today().isoformat()
    )

    assert payload["fatigue_subjective"] == 2
    assert payload["pain_level"] == 1
    assert payload["illness_status"] == "none"
    assert payload["treatment_impact"] == "none"
    assert payload["motivation"] == 4

    assert payload["notes"] == (
        "Bonne récupération."
    )


def test_daily_context_api_returns_404_when_missing() -> None:
    repository = FakeDailyContextRepository()

    client = create_client(
        repository
    )

    response = client.get(
        "/api/daily-context/today"
    )

    assert response.status_code == 404


def test_daily_context_api_saves_today() -> None:
    repository = FakeDailyContextRepository()

    client = create_client(
        repository
    )

    response = client.put(
        "/api/daily-context/today",
        json={
            "fatigue_subjective": 4,
            "pain_level": 2,
            "illness_status": "none",
            "treatment_impact": "significant",
            "motivation": 2,
            "notes": "Fatigue importante.",
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["fatigue_subjective"] == 4
    assert payload["pain_level"] == 2

    assert (
        payload["treatment_impact"]
        == "significant"
    )

    assert payload["motivation"] == 2

    assert repository.context is not None

    assert (
        repository.context.date
        == date.today()
    )


def test_daily_context_api_rejects_invalid_fatigue() -> None:
    repository = FakeDailyContextRepository()

    client = create_client(
        repository
    )

    response = client.put(
        "/api/daily-context/today",
        json={
            "fatigue_subjective": 8,
            "pain_level": 0,
            "illness_status": "none",
            "treatment_impact": "none",
            "motivation": 3,
        },
    )

    assert response.status_code == 422


def test_daily_context_api_rejects_invalid_pain() -> None:
    repository = FakeDailyContextRepository()

    client = create_client(
        repository
    )

    response = client.put(
        "/api/daily-context/today",
        json={
            "fatigue_subjective": 2,
            "pain_level": 15,
            "illness_status": "none",
            "treatment_impact": "none",
            "motivation": 3,
        },
    )

    assert response.status_code == 422


def test_daily_context_api_rejects_invalid_status() -> None:
    repository = FakeDailyContextRepository()

    client = create_client(
        repository
    )

    response = client.put(
        "/api/daily-context/today",
        json={
            "fatigue_subjective": 2,
            "pain_level": 0,
            "illness_status": "invalid",
            "treatment_impact": "none",
            "motivation": 3,
        },
    )

    assert response.status_code == 422


def test_daily_context_api_rejects_invalid_motivation() -> None:
    repository = FakeDailyContextRepository()

    client = create_client(
        repository
    )

    response = client.put(
        "/api/daily-context/today",
        json={
            "fatigue_subjective": 2,
            "pain_level": 0,
            "illness_status": "none",
            "treatment_impact": "none",
            "motivation": 0,
        },
    )

    assert response.status_code == 422
