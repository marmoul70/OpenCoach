from dataclasses import dataclass

from opencoach.planning.season.strategist_port import (
    SeasonStrategistPort,
    SeasonStrategistResponse,
)
from opencoach.planning.season.strategist_request import (
    SeasonStrategistRequest,
)


@dataclass
class FakeSeasonStrategist(
    SeasonStrategistPort
):
    """Stratège déterministe utilisé uniquement dans les tests."""

    response: SeasonStrategistResponse

    calls: int = 0

    last_request: (
        SeasonStrategistRequest | None
    ) = None

    def generate(
        self,
        *,
        request: SeasonStrategistRequest,
    ) -> SeasonStrategistResponse:
        self.calls += 1
        self.last_request = request

        return self.response