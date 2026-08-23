from abc import ABC, abstractmethod
from dataclasses import dataclass

from opencoach.planning.season.strategist_request import (
    SeasonStrategistRequest,
)


class SeasonStrategistError(RuntimeError):
    """Erreur générique du fournisseur stratégique."""


class SeasonStrategistUnavailableError(
    SeasonStrategistError
):
    """Le fournisseur stratégique n'est pas disponible."""


class SeasonStrategistInvalidResponseError(
    SeasonStrategistError
):
    """Le fournisseur stratégique a retourné une réponse inexploitable."""


@dataclass(frozen=True)
class SeasonStrategistResponse:
    """Réponse structurée brute retournée par un fournisseur stratégique."""

    content: dict[str, object]

    model: str | None = None

    raw_response: dict[str, object] | None = None


class SeasonStrategistPort(ABC):
    """Port abstrait utilisé par OpenCoach pour appeler un fournisseur stratégique optionnel."""

    @abstractmethod
    def generate(
        self,
        *,
        request: SeasonStrategistRequest,
    ) -> SeasonStrategistResponse:
        """Génère une réponse structurée depuis le fournisseur stratégique."""