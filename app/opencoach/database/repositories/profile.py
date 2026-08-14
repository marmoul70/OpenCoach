from abc import ABC, abstractmethod

from opencoach.models import AthleteProfile


class ProfileRepository(ABC):
    """Repository abstraction for athlete profiles."""

    @abstractmethod
    def get_profile(self) -> AthleteProfile:
        """Return the current athlete profile."""
        raise NotImplementedError

    @abstractmethod
    def save_profile(self, profile: AthleteProfile) -> None:
        """Persist the athlete profile."""
        raise NotImplementedError

    @abstractmethod
    def reset_profile(self) -> AthleteProfile:
        """Reset and persist the default athlete profile."""
        raise NotImplementedError
