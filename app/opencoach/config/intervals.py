import os
from dataclasses import dataclass


@dataclass(frozen=True)
class IntervalsSettings:
    """Configuration de l'intégration Intervals.icu."""

    api_key: str
    athlete_id: str

    @classmethod
    def from_env(cls) -> "IntervalsSettings":
        api_key = os.getenv("INTERVALS_API_KEY", "").strip()
        athlete_id = os.getenv(
            "INTERVALS_ATHLETE_ID",
            "",
        ).strip()

        if not api_key:
            raise RuntimeError(
                "INTERVALS_API_KEY n'est pas configurée."
            )

        if not athlete_id:
            raise RuntimeError(
                "INTERVALS_ATHLETE_ID n'est pas configuré."
            )

        return cls(
            api_key=api_key,
            athlete_id=athlete_id,
        )