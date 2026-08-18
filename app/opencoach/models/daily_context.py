from dataclasses import dataclass
from datetime import date
from typing import Literal


IllnessStatus = Literal[
    "none",
    "mild",
    "significant",
]

TreatmentImpact = Literal[
    "none",
    "mild",
    "significant",
]


@dataclass
class DailyContext:
    """Contexte subjectif quotidien renseigné par l'athlète."""

    date: date

    fatigue_subjective: int
    pain_level: int

    illness_status: IllnessStatus = "none"
    treatment_impact: TreatmentImpact = "none"

    motivation: int = 3

    notes: str | None = None
