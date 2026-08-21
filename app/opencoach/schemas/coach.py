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

class CoachRecentLoadResponse(BaseModel):
    """Synthèse de la charge d'entraînement récente."""

    analyzed_days: int

    planned_load_total: float
    actual_load_total: float

    load_delta_total: float
    load_ratio: float | None

    above_plan_days: int
    below_plan_days: int
    on_plan_days: int

    broken_rest_days: int
    respected_rest_days: int

    has_training_history: bool


class CoachRecentLoadSignalResponse(BaseModel):
    """Signal métier dérivé de la charge récente."""

    kind: str
    level: str
    reason: str


class CoachRecentLoadAssessmentResponse(BaseModel):
    """Synthèse des signaux de charge récente."""

    has_warning: bool
    has_critical: bool
    has_overload: bool
    has_broken_rest: bool

    signals: list[
        CoachRecentLoadSignalResponse
    ]

class CoachTodayResponse(BaseModel):
    date: date

    session: CoachSessionResponse | None
    readiness: CoachReadinessResponse
    decision: CoachDecisionResponse

    recent_load: (
        CoachRecentLoadResponse
        | None
    )

    recent_load_assessment: (
        CoachRecentLoadAssessmentResponse
        | None
    )
