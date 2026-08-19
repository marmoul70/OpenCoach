from dataclasses import dataclass
from typing import Literal


CoachAction = Literal[
    "keep",
    "reduce",
    "replace",
    "rest",
]


@dataclass(frozen=True)
class CoachDecision:
    """Décision d'adaptation d'une séance planifiée."""

    action: CoachAction

    reason: str

    original_duration_minutes: int | None
    recommended_duration_minutes: int | None

    duration_factor: float | None
    intensity_factor: float | None

    constraints: tuple[str, ...]

    original_intensity: str | None

    recommended_intensity: str | None
