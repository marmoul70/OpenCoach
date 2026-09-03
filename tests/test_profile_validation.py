from uuid import UUID
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from opencoach.api import create_app
from opencoach.api.profile import get_profile_service
from opencoach.database.base import Base
from opencoach.database.models import User
from opencoach.database.repositories import SqlProfileRepository
from opencoach.services import ProfileService


TEST_USER_ID = UUID(
    "00000000-0000-0000-0000-000000000001"
)


def create_test_user(
    db,
    *,
    user_id: UUID = TEST_USER_ID,
    email: str = "test@opencoach.local",
    username: str = "test001",
) -> User:
    user = User(
        id=user_id,
        email=email,
        username=username,
    )

    db.add(user)
    db.commit()

    return user


def create_client() -> TestClient:
    engine = create_engine(
        "sqlite://",
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)

    session_factory = sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )

    def get_test_profile_service():
        session = session_factory()

        try:
            if session.get(
                User,
                TEST_USER_ID,
            ) is None:
                create_test_user(
                    session,
                )

            repository = SqlProfileRepository(
                session,
                TEST_USER_ID,
            )

            yield ProfileService(
                repository,
            )
        finally:
            session.close()

    app = create_app()

    app.dependency_overrides[
        get_profile_service
    ] = get_test_profile_service

    return TestClient(app)


def valid_profile() -> dict:
    return {
        "identity": {
            "first_name": "Test",
            "last_name": "OpenCoach",
            "birth_date": "1985-01-01",
            "gender": "male",
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
            "available_days": [0, 1, 3, 5],
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


def test_valid_profile_is_accepted() -> None:
    client = create_client()

    response = client.put(
        "/api/profile",
        json=valid_profile(),
    )

    assert response.status_code == 200


def test_negative_weight_is_rejected() -> None:
    client = create_client()

    profile = valid_profile()
    profile["body"]["weight_kg"] = -10

    response = client.put(
        "/api/profile",
        json=profile,
    )

    assert response.status_code == 422


def test_invalid_vma_is_rejected() -> None:
    client = create_client()

    profile = valid_profile()
    profile["physiology"]["vma"] = 0

    response = client.put(
        "/api/profile",
        json=profile,
    )

    assert response.status_code == 422


def test_invalid_threshold_order_is_rejected() -> None:
    client = create_client()

    profile = valid_profile()
    profile["physiology"]["threshold_heart_rate_1"] = 170
    profile["physiology"]["threshold_heart_rate_2"] = 160

    response = client.put(
        "/api/profile",
        json=profile,
    )

    assert response.status_code == 422


def test_threshold_above_max_heart_rate_is_rejected() -> None:
    client = create_client()

    profile = valid_profile()
    profile["physiology"]["threshold_heart_rate_2"] = 190

    response = client.put(
        "/api/profile",
        json=profile,
    )

    assert response.status_code == 422


def test_invalid_latitude_is_rejected() -> None:
    client = create_client()

    profile = valid_profile()
    profile["location"]["latitude"] = 100

    response = client.put(
        "/api/profile",
        json=profile,
    )

    assert response.status_code == 422


def test_invalid_available_day_is_rejected() -> None:
    client = create_client()

    profile = valid_profile()
    profile["training"]["available_days"] = [0, 1, 7]

    response = client.put(
        "/api/profile",
        json=profile,
    )

    assert response.status_code == 422


def test_duplicate_available_day_is_rejected() -> None:
    client = create_client()

    profile = valid_profile()
    profile["training"]["available_days"] = [0, 1, 1]

    response = client.put(
        "/api/profile",
        json=profile,
    )

    assert response.status_code == 422


def test_future_birth_date_is_rejected() -> None:
    client = create_client()

    profile = valid_profile()
    profile["identity"]["birth_date"] = "2099-01-01"

    response = client.put(
        "/api/profile",
        json=profile,
    )

    assert response.status_code == 422


def test_resting_heart_rate_above_max_is_rejected() -> None:
    client = create_client()

    profile = valid_profile()
    profile["physiology"]["resting_heart_rate"] = 140
    profile["physiology"]["max_heart_rate"] = 130

    response = client.put(
        "/api/profile",
        json=profile,
    )

    assert response.status_code == 422


def test_sv1_above_max_heart_rate_is_rejected() -> None:
    client = create_client()

    profile = valid_profile()
    profile["physiology"]["threshold_heart_rate_1"] = 185
    profile["physiology"]["threshold_heart_rate_2"] = 190
    profile["physiology"]["max_heart_rate"] = 180

    response = client.put(
        "/api/profile",
        json=profile,
    )

    assert response.status_code == 422


def test_resting_heart_rate_above_sv1_is_rejected() -> None:
    client = create_client()

    profile = valid_profile()
    profile["physiology"]["resting_heart_rate"] = 145
    profile["physiology"]["threshold_heart_rate_1"] = 140

    response = client.put(
        "/api/profile",
        json=profile,
    )

    assert response.status_code == 422


def test_vma_above_maximum_is_rejected() -> None:
    client = create_client()

    profile = valid_profile()
    profile["physiology"]["vma"] = 41

    response = client.put(
        "/api/profile",
        json=profile,
    )

    assert response.status_code == 422


def test_resting_heart_rate_equal_max_is_rejected() -> None:
    client = create_client()

    profile = valid_profile()
    profile["physiology"]["resting_heart_rate"] = 181
    profile["physiology"]["max_heart_rate"] = 181

    response = client.put(
        "/api/profile",
        json=profile,
    )

    assert response.status_code == 422


def test_resting_heart_rate_equal_sv1_is_rejected() -> None:
    client = create_client()

    profile = valid_profile()
    profile["physiology"]["resting_heart_rate"] = 150
    profile["physiology"]["threshold_heart_rate_1"] = 150

    response = client.put(
        "/api/profile",
        json=profile,
    )

    assert response.status_code == 422


def test_sv1_equal_sv2_is_rejected() -> None:
    client = create_client()

    profile = valid_profile()
    profile["physiology"]["threshold_heart_rate_1"] = 160
    profile["physiology"]["threshold_heart_rate_2"] = 160

    response = client.put(
        "/api/profile",
        json=profile,
    )

    assert response.status_code == 422


def test_sv2_equal_max_heart_rate_is_rejected() -> None:
    client = create_client()

    profile = valid_profile()
    profile["physiology"]["threshold_heart_rate_2"] = 181
    profile["physiology"]["max_heart_rate"] = 181

    response = client.put(
        "/api/profile",
        json=profile,
    )

    assert response.status_code == 422


def test_resting_heart_rate_without_max_is_accepted() -> None:
    client = create_client()

    profile = valid_profile()
    profile["physiology"]["max_heart_rate"] = None
    profile["physiology"]["resting_heart_rate"] = 50

    response = client.put(
        "/api/profile",
        json=profile,
    )

    assert response.status_code == 200


def test_sv1_without_sv2_is_accepted() -> None:
    client = create_client()

    profile = valid_profile()
    profile["physiology"]["threshold_heart_rate_2"] = None
    profile["physiology"]["threshold_heart_rate_1"] = 150

    response = client.put(
        "/api/profile",
        json=profile,
    )

    assert response.status_code == 200


def test_sv2_without_max_heart_rate_is_accepted() -> None:
    client = create_client()

    profile = valid_profile()
    profile["physiology"]["max_heart_rate"] = None
    profile["physiology"]["threshold_heart_rate_2"] = 165

    response = client.put(
        "/api/profile",
        json=profile,
    )

    assert response.status_code == 200


def test_negative_shoe_distance_is_rejected() -> None:
    client = create_client()

    profile = valid_profile()
    profile["equipment"]["shoes"] = [
        {
            "id": "shoe-1",
            "model": "Trail",
            "brand": "Test",
            "active": True,
            "distance_km": -1,
            "max_distance_km": 800,
        }
    ]

    response = client.put(
        "/api/profile",
        json=profile,
    )

    assert response.status_code == 422


def test_shoe_max_distance_below_distance_is_rejected() -> None:
    client = create_client()

    profile = valid_profile()
    profile["equipment"]["shoes"] = [
        {
            "id": "shoe-1",
            "model": "Trail",
            "brand": "Test",
            "active": True,
            "distance_km": 500,
            "max_distance_km": 400,
        }
    ]

    response = client.put(
        "/api/profile",
        json=profile,
    )

    assert response.status_code == 422


def test_shoe_max_distance_equal_distance_is_accepted() -> None:
    client = create_client()

    profile = valid_profile()
    profile["equipment"]["shoes"] = [
        {
            "id": "shoe-1",
            "model": "Trail",
            "brand": "Test",
            "active": True,
            "distance_km": 500,
            "max_distance_km": 500,
        }
    ]

    response = client.put(
        "/api/profile",
        json=profile,
    )

    assert response.status_code == 200


def test_negative_bike_distance_is_rejected() -> None:
    client = create_client()

    profile = valid_profile()
    profile["equipment"]["bikes"] = [
        {
            "id": "bike-1",
            "model": "Gravel",
            "brand": "Test",
            "active": True,
            "distance_km": -1,
        }
    ]

    response = client.put(
        "/api/profile",
        json=profile,
    )

    assert response.status_code == 422


def test_empty_equipment_id_is_rejected() -> None:
    client = create_client()

    profile = valid_profile()
    profile["equipment"]["shoes"] = [
        {
            "id": "",
            "model": "Trail",
            "brand": "Test",
            "active": True,
            "distance_km": 0,
            "max_distance_km": 800,
        }
    ]

    response = client.put(
        "/api/profile",
        json=profile,
    )

    assert response.status_code == 422


def test_empty_equipment_model_is_rejected() -> None:
    client = create_client()

    profile = valid_profile()
    profile["equipment"]["bikes"] = [
        {
            "id": "bike-1",
            "model": "",
            "brand": "Test",
            "active": True,
            "distance_km": 0,
        }
    ]

    response = client.put(
        "/api/profile",
        json=profile,
    )

    assert response.status_code == 422


def test_valid_equipment_is_accepted() -> None:
    client = create_client()

    profile = valid_profile()
    profile["equipment"] = {
        "shoes": [
            {
                "id": "shoe-1",
                "model": "Trabuco",
                "brand": "ASICS",
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
                "model": "Race",
                "brand": "Suunto",
                "active": True,
            }
        ],
    }

    response = client.put(
        "/api/profile",
        json=profile,
    )

    assert response.status_code == 200


def test_invalid_gender_is_rejected() -> None:
    client = create_client()

    profile = valid_profile()
    profile["identity"]["gender"] = "invalid"

    response = client.put(
        "/api/profile",
        json=profile,
    )

    assert response.status_code == 422


def test_invalid_birth_date_is_rejected() -> None:
    client = create_client()

    profile = valid_profile()
    profile["identity"]["birth_date"] = "01/01/1985"

    response = client.put(
        "/api/profile",
        json=profile,
    )

    assert response.status_code == 422


def test_name_whitespace_is_stripped() -> None:
    client = create_client()

    profile = valid_profile()
    profile["identity"]["first_name"] = "  Jean  "
    profile["identity"]["last_name"] = "  Dupont  "

    response = client.put(
        "/api/profile",
        json=profile,
    )

    assert response.status_code == 200
    assert response.json()["identity"]["first_name"] == "Jean"
    assert response.json()["identity"]["last_name"] == "Dupont"


def test_invalid_long_first_name_is_rejected() -> None:
    client = create_client()

    profile = valid_profile()
    profile["identity"]["first_name"] = "A" * 101

    response = client.put(
        "/api/profile",
        json=profile,
    )

    assert response.status_code == 422


def test_invalid_long_last_name_is_rejected() -> None:
    client = create_client()

    profile = valid_profile()
    profile["identity"]["last_name"] = "A" * 101

    response = client.put(
        "/api/profile",
        json=profile,
    )

    assert response.status_code == 422


def test_invalid_longitude_is_rejected() -> None:
    client = create_client()

    profile = valid_profile()
    profile["location"]["longitude"] = 181

    response = client.put(
        "/api/profile",
        json=profile,
    )

    assert response.status_code == 422


def test_invalid_training_experience_is_rejected() -> None:
    client = create_client()

    profile = valid_profile()
    profile["training"]["experience"] = "professional"

    response = client.put(
        "/api/profile",
        json=profile,
    )

    assert response.status_code == 422


def test_negative_weekly_sessions_is_rejected() -> None:
    client = create_client()

    profile = valid_profile()
    profile["training"]["weekly_sessions"] = -1

    response = client.put(
        "/api/profile",
        json=profile,
    )

    assert response.status_code == 422


def test_negative_weekly_duration_is_rejected() -> None:
    client = create_client()

    profile = valid_profile()
    profile["training"]["weekly_duration_minutes"] = -1

    response = client.put(
        "/api/profile",
        json=profile,
    )

    assert response.status_code == 422


def test_negative_weekly_distance_is_rejected() -> None:
    client = create_client()

    profile = valid_profile()
    profile["training"]["weekly_distance_km"] = -1

    response = client.put(
        "/api/profile",
        json=profile,
    )

    assert response.status_code == 422


def test_negative_fatigue_threshold_is_rejected() -> None:
    client = create_client()

    profile = valid_profile()
    profile["training"]["fatigue_threshold"] = -1

    response = client.put(
        "/api/profile",
        json=profile,
    )

    assert response.status_code == 422


def test_negative_carbohydrates_per_hour_is_rejected() -> None:
    client = create_client()

    profile = valid_profile()
    profile["nutrition"]["carbohydrates_per_hour"] = -1

    response = client.put(
        "/api/profile",
        json=profile,
    )

    assert response.status_code == 422


def test_negative_fluids_per_hour_is_rejected() -> None:
    client = create_client()

    profile = valid_profile()
    profile["nutrition"]["fluids_per_hour"] = -1

    response = client.put(
        "/api/profile",
        json=profile,
    )

    assert response.status_code == 422


def test_negative_sodium_per_hour_is_rejected() -> None:
    client = create_client()

    profile = valid_profile()
    profile["nutrition"]["sodium_per_hour"] = -1

    response = client.put(
        "/api/profile",
        json=profile,
    )

    assert response.status_code == 422


def test_zero_nutrition_values_are_accepted() -> None:
    client = create_client()

    profile = valid_profile()
    profile["nutrition"] = {
        "carbohydrates_per_hour": 0,
        "fluids_per_hour": 0,
        "sodium_per_hour": 0,
    }

    response = client.put(
        "/api/profile",
        json=profile,
    )

    assert response.status_code == 200
