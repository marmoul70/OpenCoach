from pathlib import Path
from copy import deepcopy

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from opencoach.api import create_app
from opencoach.api.profile import get_profile_service
from opencoach.database.base import Base
from opencoach.database.repositories import (
    ProfileRepositoryError,
    SqlProfileRepository,
)
from opencoach.services import ProfileService


def create_test_client(tmp_path: Path) -> TestClient:
    database_path = tmp_path / "opencoach-test.db"

    engine = create_engine(
        f"sqlite:///{database_path}",
        connect_args={"check_same_thread": False},
    )

    Base.metadata.create_all(engine)

    session_factory = sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )

    def get_test_profile_service() -> ProfileService:
        session = session_factory()
        repository = SqlProfileRepository(session)

        return ProfileService(repository)

    app = create_app()

    app.dependency_overrides[get_profile_service] = (
        get_test_profile_service
    )

    return TestClient(app)

class FailingProfileService:
    """Simule une indisponibilité de la persistance du profil."""

    def get_profile(self):
        raise ProfileRepositoryError("database unavailable")

    def update_profile(self, profile):
        raise ProfileRepositoryError("database unavailable")

    def reset_profile(self):
        raise ProfileRepositoryError("database unavailable")


def create_failing_test_client() -> TestClient:
    app = create_app()

    app.dependency_overrides[get_profile_service] = (
        lambda: FailingProfileService()
    )

    return TestClient(app)

def test_get_profile_returns_default_profile(tmp_path: Path) -> None:
    client = create_test_client(tmp_path)

    response = client.get("/api/profile")

    assert response.status_code == 200

    data = response.json()

    assert data["identity"]["first_name"] == ""
    assert data["identity"]["last_name"] == ""
    assert data["body"]["weight_kg"] is None


def test_put_profile_persists_profile(tmp_path: Path) -> None:
    client = create_test_client(tmp_path)

    profile = {
        "identity": {
            "first_name": "Test",
            "last_name": "OpenCoach",
            "birth_date": "",
            "gender": "unspecified",
            "avatar": None,
        },
        "body": {
            "height_cm": 185,
            "weight_kg": 85,
        },
        "physiology": {
            "max_heart_rate": 181,
            "resting_heart_rate": 50,
            "vma": 15,
            "threshold_heart_rate_1": 150,
            "threshold_heart_rate_2": 165,
        },
        "training": {
            "weekly_sessions": 4,
            "weekly_duration_minutes": 300,
            "weekly_distance_km": 50,
            "available_days": [1, 2, 4, 6],
            "fatigue_threshold": 7,
            "experience": "advanced",
        },
        "location": {
            "name": "Belfort",
            "latitude": 47.6397,
            "longitude": 6.8638,
        },
        "equipment": {
            "shoes": [],
            "bikes": [],
            "watches": [],
        },
        "nutrition": {
            "carbohydrates_per_hour": 60,
            "fluids_per_hour": 500,
            "sodium_per_hour": 500,
        },
    }

    response = client.put(
        "/api/profile",
        json=profile,
    )

    assert response.status_code == 200

    saved = response.json()

    assert saved["identity"]["first_name"] == "Test"
    assert saved["body"]["weight_kg"] == 85
    assert saved["physiology"]["vma"] == 15

    response = client.get("/api/profile")

    assert response.status_code == 200

    loaded = response.json()

    assert loaded["identity"]["first_name"] == "Test"
    assert loaded["identity"]["last_name"] == "OpenCoach"
    assert loaded["body"]["weight_kg"] == 85
    assert loaded["physiology"]["vma"] == 15


def test_put_profile_rejects_invalid_gender(tmp_path: Path) -> None:
    client = create_test_client(tmp_path)

    profile = {
        "identity": {
            "first_name": "Test",
            "last_name": "OpenCoach",
            "birth_date": "",
            "gender": "invalid",
            "avatar": None,
        },
        "body": {},
        "physiology": {},
        "training": {
            "available_days": [],
            "experience": "beginner",
        },
        "location": {},
        "equipment": {
            "shoes": [],
            "bikes": [],
            "watches": [],
        },
        "nutrition": {},
    }

    response = client.put(
        "/api/profile",
        json=profile,
    )

    assert response.status_code == 422

def test_reset_profile_returns_default_profile(tmp_path: Path) -> None:
    client = create_test_client(tmp_path)

    profile = {
        "identity": {
            "first_name": "Test",
            "last_name": "OpenCoach",
            "birth_date": "",
            "gender": "unspecified",
            "avatar": None,
        },
        "body": {
            "height_cm": 185,
            "weight_kg": 85,
        },
        "physiology": {
            "vma": 15,
        },
        "training": {
            "available_days": [],
            "experience": "advanced",
        },
        "location": {},
        "equipment": {
            "shoes": [],
            "bikes": [],
            "watches": [],
        },
        "nutrition": {},
    }

    response = client.put(
        "/api/profile",
        json=profile,
    )

    assert response.status_code == 200

    response = client.post("/api/profile/reset")

    assert response.status_code == 200

    data = response.json()

    assert data["identity"]["first_name"] == ""
    assert data["identity"]["last_name"] == ""
    assert data["body"]["weight_kg"] is None
    assert data["physiology"]["vma"] is None

    response = client.get("/api/profile")

    assert response.status_code == 200

    loaded = response.json()

    assert loaded["identity"]["first_name"] == ""
    assert loaded["body"]["weight_kg"] is None
    assert loaded["physiology"]["vma"] is None

def test_put_invalid_profile_does_not_overwrite_existing_profile(
    tmp_path: Path,
) -> None:
    client = create_test_client(tmp_path)

    valid_profile = {
        "identity": {
            "first_name": "Test",
            "last_name": "OpenCoach",
            "birth_date": "",
            "gender": "unspecified",
            "avatar": None,
        },
        "body": {
            "height_cm": 185,
            "weight_kg": 85,
        },
        "physiology": {
            "max_heart_rate": 181,
            "resting_heart_rate": 50,
            "vma": 15,
            "threshold_heart_rate_1": 150,
            "threshold_heart_rate_2": 165,
        },
        "training": {
            "weekly_sessions": 4,
            "weekly_duration_minutes": 300,
            "weekly_distance_km": 50,
            "available_days": [1, 2, 4, 6],
            "fatigue_threshold": 7,
            "experience": "advanced",
        },
        "location": {
            "name": "Belfort",
            "latitude": 47.6397,
            "longitude": 6.8638,
        },
        "equipment": {
            "shoes": [],
            "bikes": [],
            "watches": [],
        },
        "nutrition": {
            "carbohydrates_per_hour": 60,
            "fluids_per_hour": 500,
            "sodium_per_hour": 500,
        },
    }

    response = client.put(
        "/api/profile",
        json=valid_profile,
    )

    assert response.status_code == 200

    invalid_profile = {
        **valid_profile,
        "body": {
            **valid_profile["body"],
            "weight_kg": -10,
        },
    }

    response = client.put(
        "/api/profile",
        json=invalid_profile,
    )

    assert response.status_code == 422

    response = client.get("/api/profile")

    assert response.status_code == 200

    data = response.json()

    assert data["body"]["weight_kg"] == 85
    assert data["identity"]["first_name"] == "Test"


def test_put_and_get_profile_with_equipment(tmp_path: Path) -> None:
    client = create_test_client(tmp_path)

    profile = {
        "identity": {
            "first_name": "Test",
            "last_name": "OpenCoach",
            "birth_date": "",
            "gender": "unspecified",
            "avatar": None,
        },
        "body": {},
        "physiology": {},
        "training": {
            "available_days": [],
            "experience": "advanced",
        },
        "location": {},
        "equipment": {
            "shoes": [
                {
                    "id": "shoe-1",
                    "model": "Trabuco 13",
                    "brand": "Asics",
                    "active": True,
                    "distance_km": 250,
                    "max_distance_km": 800,
                }
            ],
            "bikes": [
                {
                    "id": "bike-1",
                    "model": "Nuroad",
                    "brand": "Cube",
                    "active": True,
                    "distance_km": 1200,
                }
            ],
            "watches": [
                {
                    "id": "watch-1",
                    "model": "Race 2",
                    "brand": "Suunto",
                    "active": True,
                }
            ],
        },
        "nutrition": {},
    }

    response = client.put(
        "/api/profile",
        json=profile,
    )

    assert response.status_code == 200

    response = client.get("/api/profile")

    assert response.status_code == 200

    data = response.json()

    assert data["equipment"]["shoes"][0]["id"] == "shoe-1"
    assert data["equipment"]["shoes"][0]["model"] == "Trabuco 13"
    assert data["equipment"]["shoes"][0]["distance_km"] == 250
    assert data["equipment"]["shoes"][0]["max_distance_km"] == 800

    assert data["equipment"]["bikes"][0]["id"] == "bike-1"
    assert data["equipment"]["bikes"][0]["model"] == "Nuroad"
    assert data["equipment"]["bikes"][0]["distance_km"] == 1200

    assert data["equipment"]["watches"][0]["id"] == "watch-1"
    assert data["equipment"]["watches"][0]["model"] == "Race 2"
    assert data["equipment"]["watches"][0]["brand"] == "Suunto"

def test_put_invalid_profile_does_not_overwrite_existing_profile(
    tmp_path: Path,
) -> None:
    client = create_test_client(tmp_path)

    valid_profile = {
        "identity": {
            "first_name": "Original",
            "last_name": "Profile",
            "birth_date": "",
            "gender": "unspecified",
            "avatar": None,
        },
        "body": {
            "height_cm": 185,
            "weight_kg": 85,
        },
        "physiology": {
            "max_heart_rate": 181,
            "resting_heart_rate": 50,
            "vma": 15,
            "threshold_heart_rate_1": 150,
            "threshold_heart_rate_2": 165,
        },
        "training": {
            "weekly_sessions": 4,
            "weekly_duration_minutes": 300,
            "weekly_distance_km": 50,
            "available_days": [1, 2, 4, 6],
            "fatigue_threshold": 7,
            "experience": "advanced",
        },
        "location": {
            "name": "Belfort",
            "latitude": 47.6397,
            "longitude": 6.8638,
        },
        "equipment": {
            "shoes": [],
            "bikes": [],
            "watches": [],
        },
        "nutrition": {
            "carbohydrates_per_hour": 60,
            "fluids_per_hour": 500,
            "sodium_per_hour": 500,
        },
    }

    response = client.put(
        "/api/profile",
        json=valid_profile,
    )

    assert response.status_code == 200

    invalid_profile = deepcopy(valid_profile)
    invalid_profile["body"] = {
        "height_cm": 185,
        "weight_kg": -10,
    }

    response = client.put(
        "/api/profile",
        json=invalid_profile,
    )

    assert response.status_code == 422

    response = client.get("/api/profile")

    assert response.status_code == 200

    data = response.json()

    assert data["identity"]["first_name"] == "Original"
    assert data["body"]["weight_kg"] == 85


def test_put_and_get_profile_with_equipment(
    tmp_path: Path,
) -> None:
    client = create_test_client(tmp_path)

    profile = {
        "identity": {
            "first_name": "Test",
            "last_name": "Equipment",
            "birth_date": "",
            "gender": "unspecified",
            "avatar": None,
        },
        "body": {},
        "physiology": {},
        "training": {
            "available_days": [],
            "experience": "beginner",
        },
        "location": {},
        "equipment": {
            "shoes": [
                {
                    "id": "shoe-1",
                    "model": "Trabuco",
                    "brand": "Asics",
                    "active": True,
                    "distance_km": 120,
                    "max_distance_km": 800,
                }
            ],
            "bikes": [
                {
                    "id": "bike-1",
                    "model": "Nuroad",
                    "brand": "Cube",
                    "active": True,
                    "distance_km": 500,
                }
            ],
            "watches": [
                {
                    "id": "watch-1",
                    "model": "Race",
                    "brand": "Suunto",
                    "active": True,
                }
            ],
        },
        "nutrition": {},
    }

    response = client.put(
        "/api/profile",
        json=profile,
    )

    assert response.status_code == 200

    response = client.get("/api/profile")

    assert response.status_code == 200

    data = response.json()

    assert len(data["equipment"]["shoes"]) == 1
    assert data["equipment"]["shoes"][0]["id"] == "shoe-1"

    assert len(data["equipment"]["bikes"]) == 1
    assert data["equipment"]["bikes"][0]["id"] == "bike-1"

    assert len(data["equipment"]["watches"]) == 1
    assert data["equipment"]["watches"][0]["id"] == "watch-1"

def test_get_profile_returns_503_when_storage_fails() -> None:
    client = create_failing_test_client()

    response = client.get("/api/profile")

    assert response.status_code == 503
    assert response.json() == {
        "detail": (
            "Le stockage du profil est temporairement indisponible."
        )
    }


def test_put_profile_returns_503_when_storage_fails() -> None:
    client = create_failing_test_client()

    profile = {
        "identity": {
            "first_name": "Test",
            "last_name": "OpenCoach",
            "birth_date": "",
            "gender": "unspecified",
            "avatar": None,
        },
        "body": {},
        "physiology": {},
        "training": {
            "available_days": [],
            "experience": "beginner",
        },
        "location": {},
        "equipment": {
            "shoes": [],
            "bikes": [],
            "watches": [],
        },
        "nutrition": {},
    }

    response = client.put(
        "/api/profile",
        json=profile,
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": (
            "Le stockage du profil est temporairement indisponible."
        )
    }


def test_reset_profile_returns_503_when_storage_fails() -> None:
    client = create_failing_test_client()

    response = client.post("/api/profile/reset")

    assert response.status_code == 503
    assert response.json() == {
        "detail": (
            "Le stockage du profil est temporairement indisponible."
        )
    }