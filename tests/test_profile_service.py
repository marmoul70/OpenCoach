from opencoach.models import AthleteProfile
from opencoach.services import ProfileService


class FakeProfileRepository:
    def __init__(self) -> None:
        self.profile = AthleteProfile()
        self.saved_profile: AthleteProfile | None = None
        self.reset_called = False

    def get_profile(self) -> AthleteProfile:
        return self.profile

    def save_profile(self, profile: AthleteProfile) -> None:
        self.saved_profile = profile

    def reset_profile(self) -> AthleteProfile:
        self.reset_called = True
        self.profile = AthleteProfile()
        return self.profile


def test_service_returns_profile_from_repository() -> None:
    repository = FakeProfileRepository()
    repository.profile.identity.first_name = "Test"

    service = ProfileService(repository)

    profile = service.get_profile()

    assert profile.identity.first_name == "Test"


def test_service_updates_profile_through_repository() -> None:
    repository = FakeProfileRepository()
    service = ProfileService(repository)

    profile = AthleteProfile()
    profile.identity.first_name = "Seby"
    profile.body.weight_kg = 85

    result = service.update_profile(profile)

    assert result is profile
    assert repository.saved_profile is profile


def test_service_resets_profile_through_repository() -> None:
    repository = FakeProfileRepository()
    repository.profile.identity.first_name = "Modified"

    service = ProfileService(repository)

    result = service.reset_profile()

    assert repository.reset_called is True
    assert result.identity.first_name == ""
