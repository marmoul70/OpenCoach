import json
from pathlib import Path

import pytest

from opencoach.database.repositories import JsonProfileRepository


def write_profile(path: Path, profile: dict) -> None:
    path.write_text(
        json.dumps(profile),
        encoding="utf-8",
    )


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


def test_valid_json_profile_is_loaded(tmp_path: Path) -> None:
    path = tmp_path / "profile.json"
    write_profile(path, valid_profile())

    profile = JsonProfileRepository(path).get_profile()

    assert profile.identity.first_name == "Test"
    assert profile.body.weight_kg == 85
    assert profile.physiology.vma == 15


def test_invalid_json_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "profile.json"
    path.write_text("{invalid json", encoding="utf-8")

    repository = JsonProfileRepository(path)

    with pytest.raises(ValueError):
        repository.get_profile()


def test_negative_weight_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "profile.json"

    profile = valid_profile()
    profile["body"]["weight_kg"] = -10

    write_profile(path, profile)

    with pytest.raises(ValueError):
        JsonProfileRepository(path).get_profile()


def test_invalid_threshold_order_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "profile.json"

    profile = valid_profile()
    profile["physiology"]["threshold_heart_rate_1"] = 170
    profile["physiology"]["threshold_heart_rate_2"] = 160

    write_profile(path, profile)

    with pytest.raises(ValueError):
        JsonProfileRepository(path).get_profile()


def test_unknown_field_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "profile.json"

    profile = valid_profile()
    profile["body"]["unknown_field"] = 123

    write_profile(path, profile)

    with pytest.raises(ValueError):
        JsonProfileRepository(path).get_profile()


def test_missing_profile_creates_default_profile(tmp_path: Path) -> None:
    path = tmp_path / "profile.json"

    repository = JsonProfileRepository(path)

    profile = repository.get_profile()

    assert isinstance(profile, type(repository.reset_profile()))
    assert path.exists()
    assert profile.identity.first_name == ""
    assert profile.body.weight_kg is None


def test_save_and_reload_profile_preserves_data(tmp_path: Path) -> None:
    path = tmp_path / "profile.json"

    repository = JsonProfileRepository(path)

    profile = repository.get_profile()
    profile.identity.first_name = "Seb"
    profile.body.weight_kg = 85
    profile.physiology.vma = 15

    repository.save_profile(profile)

    reloaded = repository.get_profile()

    assert reloaded.identity.first_name == "Seb"
    assert reloaded.body.weight_kg == 85
    assert reloaded.physiology.vma == 15


@pytest.mark.parametrize(
    "content",
    [
        "[]",
        '"profile"',
        "123",
        "null",
    ],
)
def test_non_object_json_is_rejected(
    tmp_path: Path,
    content: str,
) -> None:
    path = tmp_path / "profile.json"
    path.write_text(content, encoding="utf-8")

    with pytest.raises(ValueError):
        JsonProfileRepository(path).get_profile()


def test_unknown_root_field_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "profile.json"

    profile = valid_profile()
    profile["unknown_field"] = 123

    write_profile(path, profile)

    with pytest.raises(ValueError):
        JsonProfileRepository(path).get_profile()


def test_invalid_equipment_item_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "profile.json"

    profile = valid_profile()
    profile["equipment"]["shoes"] = [
        {
            "id": "",
            "model": "Trail Shoe",
            "brand": "Test",
            "active": True,
            "distance_km": 10,
            "max_distance_km": 500,
        }
    ]

    write_profile(path, profile)

    with pytest.raises(ValueError):
        JsonProfileRepository(path).get_profile()


def test_reset_profile_replaces_existing_profile(tmp_path: Path) -> None:
    path = tmp_path / "profile.json"

    repository = JsonProfileRepository(path)

    profile = repository.get_profile()
    profile.identity.first_name = "Seb"
    profile.body.weight_kg = 85

    repository.save_profile(profile)

    reset = repository.reset_profile()

    assert reset.identity.first_name == ""
    assert reset.body.weight_kg is None

    reloaded = repository.get_profile()

    assert reloaded.identity.first_name == ""
    assert reloaded.body.weight_kg is None
