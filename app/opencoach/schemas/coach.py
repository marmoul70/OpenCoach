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

    source_date: date
    data_age_days: int
    data_status: str


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

class CoachSessionDecisionResponse(BaseModel):
    """Décision du coach associée à une séance."""

    session: CoachSessionResponse | None
    decision: CoachDecisionResponse


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

class CoachWeeklyAssessmentResponse(BaseModel):
    """Évaluation de la trajectoire hebdomadaire du Coach."""

    status: str

    target_load: float | None
    actual_load_to_date: float
    remaining_planned_load: float
    projected_week_load: float

    projected_gap: float | None
    projected_gap_percent: float | None

    remaining_days: int
    remaining_sessions_count: int

    adaptation_opportunity: bool
    adaptation_direction: str | None

    history_window_days: int
    history_confidence: float
    history_confidence_level: str

    headline: str
    analysis: str
    instruction: str


class CoachWeeklyPlanResponse(BaseModel):
    """Intention persistée du plan hebdomadaire OpenCoach."""

    week_start: date
    week_end: date

    phase: str
    week_type: str | None
    phase_week_index: int


class CoachTrajectoryWeekResponse(BaseModel):
    """Une semaine de progression OpenCoach."""

    week_start: date
    week_end: date

    mode: str

    phase: str
    week_type: str
    phase_week_index: int

    target_load: float
    load_min: float
    load_max: float


class CoachTrajectoryResponse(BaseModel):
    """Progression continue jusqu'à la prochaine course principale."""

    target_race_name: str
    target_race_date: date

    preparation_start_date: date

    weeks: list[
        CoachTrajectoryWeekResponse
    ]


class CoachTodayResponse(BaseModel):
    date: date

    session_decisions: list[
        CoachSessionDecisionResponse
    ]

    readiness: CoachReadinessResponse

    recent_load: (
        CoachRecentLoadResponse
        | None
    )

    recent_load_assessment: (
        CoachRecentLoadAssessmentResponse
        | None
    )

    weekly_assessment: CoachWeeklyAssessmentResponse

    weekly_plan: CoachWeeklyPlanResponse | None

    data_warning: str | None
