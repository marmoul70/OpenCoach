from dataclasses import dataclass
from datetime import date
from typing import Literal
from uuid import UUID


PhysiologicalMetric = Literal[
    "vma",
    "max_heart_rate",
    "resting_heart_rate",
    "threshold_heart_rate_1",
    "threshold_heart_rate_2",
]

MeasurementSource = Literal[
    "field_test",
    "laboratory",
    "device",
    "imported",
    "estimated",
    "manual",
]

MeasurementConfidence = Literal[
    "low",
    "medium",
    "high",
]


@dataclass(frozen=True)
class PhysiologicalMeasurement:
    """Mesure physiologique historisée d'un athlète."""

    id: UUID

    metric: PhysiologicalMetric
    value: float

    measured_at: date

    protocol: str | None = None
    source: MeasurementSource = "manual"
    confidence: MeasurementConfidence = "medium"

    notes: str | None = None

    def __post_init__(self) -> None:
        if self.value <= 0:
            raise ValueError(
                "La valeur physiologique doit être strictement positive."
            )

        if self.protocol is not None:
            normalized_protocol = (
                self.protocol.strip().lower()
            )

            if not normalized_protocol:
                raise ValueError(
                    "Le protocole ne peut pas être vide."
                )

            object.__setattr__(
                self,
                "protocol",
                normalized_protocol,
            )
