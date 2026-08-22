from abc import ABC, abstractmethod
from dataclasses import dataclass

from .season_strategist_request import (
    SeasonStrategistRequest,
)


class SeasonStrategistError(RuntimeError):
    """Erreur générique du stratège IA."""


class SeasonStrategistUnavailableError(
    SeasonStrategistError
):
    """Le moteur IA local n'est pas disponible."""


class SeasonStrategistInvalidResponseError(
    SeasonStrategistError
):
    """Le moteur IA a retourné une réponse inexploitable."""


@dataclass(frozen=True)
class SeasonStrategistResponse:
    """Réponse structurée brute retournée par un moteur IA."""

    content: dict[str, object]

    model: str | None = None

    raw_response: dict[str, object] | None = None


class SeasonStrategistPort(ABC):
    """Port abstrait utilisé par OpenCoach pour appeler le stratège IA."""

    @abstractmethod
    def generate(
        self,
        *,
        request: SeasonStrategistRequest,
    ) -> SeasonStrategistResponse:
        """Génère une réponse structurée depuis le moteur IA."""