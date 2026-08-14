from pathlib import Path

from opencoach.database.repositories import JsonProfileRepository
from opencoach.models import AthleteProfile


def test_repository_returns_profile_when_file_does_not_exist(
    tmp_path: Path,
) -> None:
    repository = JsonProfileRepository(
        tmp_path / "profile.json",
    )

    profile = repository.get_profile()

    assert isinstance(profile, AthleteProfile)


def test_repository_saves_and_reads_profile(
    tmp_path: Path,
) -> None:
    repository = JsonProfileRepository(
        tmp_path / "profile.json",
    )

    profile = repository.get_profile()
    profile.identity.first_name = "Test"
    profile.identity.last_name = "Repository"
    profile.body.weight_kg = 85
    profile.physiology.vma = 15

    repository.save_profile(profile)

    loaded_profile = repository.get_profile()

    assert loaded_profile.identity.first_name == "Test"
    assert loaded_profile.identity.last_name == "Repository"
    assert loaded_profile.body.weight_kg == 85
    assert loaded_profile.physiology.vma == 15


def test_repository_reset_restores_default_profile(
    tmp_path: Path,
) -> None:
    repository = JsonProfileRepository(
        tmp_path / "profile.json",
    )

    profile = repository.get_profile()
    profile.identity.first_name = "Modified"
    profile.body.weight_kg = 99

    repository.save_profile(profile)

    reset_profile = repository.reset_profile()

    assert reset_profile.identity.first_name != "Modified"
    assert reset_profile.body.weight_kg != 99

    loaded_profile = repository.get_profile()

    assert loaded_profile.identity.first_name != "Modified"
    assert loaded_profile.body.weight_kg != 99
