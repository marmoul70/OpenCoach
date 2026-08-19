from datetime import date
from uuid import UUID

from pydantic import BaseModel


class CoachSessionResponse(BaseModel):
    id: UUID | None

    date: date
    type: str
    sport_type: str

    title: str
    description: str

    duration_minutes: int

    distance_km: float | None
    elevation_gain_m: float | None

    intensity: str
    heart_rate_zone: str | None

    status: str

class CoachReadinessSignalResponse(BaseModel):
    """Signal individuel ayant participé au Readiness."""

    metric: str
    level: str
    reason: str

    current_value: float | None
    reference_value: float | None

class CoachReadinessResponse(BaseModel):
    score: float
    level: str

    warning_count: int
    critical_count: int

    training_constraints: list[str]

    signals: list[CoachReadinessSignalResponse]


class CoachDecisionResponse(BaseModel):
    action: str
    reason: str

    original_duration_minutes: int | None
    recommended_duration_minutes: int | None

    duration_factor: float | None
    intensity_factor: float | None

    original_intensity: str | None
    recommended_intensity: str | None

    constraints: list[str]


class CoachTodayResponse(BaseModel):
    date: date

    session: CoachSessionResponse | None
    readiness: CoachReadinessResponse
    decision: CoachDecisionResponse
