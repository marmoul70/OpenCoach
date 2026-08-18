from datetime import date

from pydantic import BaseModel


class MetricBaselineResponse(BaseModel):
    median: float | None
    sample_count: int
    reliable: bool


class MetricComparisonResponse(BaseModel):
    current: float | None
    baseline: float | None
    absolute_delta: float | None
    percent_delta: float | None
    reliable: bool


class ReadinessSignalResponse(BaseModel):
    metric: str
    level: str
    reason: str
    current_value: float | None
    reference_value: float | None


class DailyReadinessResponse(BaseModel):
    score: float
    level: str

    warning_count: int
    critical_count: int

    training_constraints: list[str]

    fitness_ctl: float | None
    fatigue_atl: float | None
    training_balance: float | None

    signals: list[ReadinessSignalResponse]


class ReadinessBaselineResponse(BaseModel):
    start_date: date
    end_date: date

    hrv: MetricBaselineResponse
    resting_hr: MetricBaselineResponse
    sleep_seconds: MetricBaselineResponse
    sleep_score: MetricBaselineResponse


class ReadinessComparisonResponse(BaseModel):
    hrv: MetricComparisonResponse
    resting_hr: MetricComparisonResponse
    sleep_seconds: MetricComparisonResponse
    sleep_score: MetricComparisonResponse


class ReadinessAssessmentResponse(BaseModel):
    date: date
    provider: str

    baseline: ReadinessBaselineResponse
    comparison: ReadinessComparisonResponse
    readiness: DailyReadinessResponse
