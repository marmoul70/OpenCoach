from opencoach.database.repositories import ProfileRepository
from opencoach.models import AthleteProfile


class ProfileService:
    """Business service for athlete profile operations."""

    def __init__(self, repository: ProfileRepository) -> None:
        self.repository = repository

    def get_profile(self) -> AthleteProfile:
        return self.repository.get_profile()

    def update_profile(
        self,
        profile: AthleteProfile,
    ) -> AthleteProfile:
        self.repository.save_profile(profile)
        return profile

    def reset_profile(self) -> AthleteProfile:
        return self.repository.reset_profile()
