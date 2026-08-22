from dataclasses import dataclass
from datetime import date
from typing import Literal
from uuid import UUID


ConstraintType = Literal[
    "injury",
    "illness",
    "work",
    "travel",
    "family",
    "personal",
    "other",
]

TrainingAvailability = Literal[
    "unavailable",
    "limited",
    "available_override",
]


@dataclass(frozen=True)
class AthleteConstraint:
    """Contrainte temporaire affectant la disponibilité de l'athlète."""

    id: UUID

    start_date: date
    end_date: date

    constraint_type: ConstraintType
    availability: TrainingAvailability

    running_allowed: bool = True
    cross_training_allowed: bool = True

    max_duration_minutes: int | None = None

    notes: str | None = None

    def __post_init__(self) -> None:
        if self.end_date < self.start_date:
            raise ValueError(
                "La date de fin ne peut pas précéder la date de début."
            )

        if (
            self.max_duration_minutes is not None
            and self.max_duration_minutes < 0
        ):
            raise ValueError(
                "La durée maximale ne peut pas être négative."
            )

    def is_active_on(
        self,
        target_date: date,
    ) -> bool:
        """Indique si la contrainte est active à une date donnée."""
        return (
            self.start_date
            <= target_date
            <= self.end_date
        )
