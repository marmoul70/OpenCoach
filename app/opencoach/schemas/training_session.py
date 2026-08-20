from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field

class TrainingSessionCreate(BaseModel):
    date: date

    type: str = Field(
        default="supplementary",
        min_length=1,
        max_length=50,
    )

    sport_type: str = Field(
        min_length=1,
        max_length=100,
    )

    title: str = Field(
        min_length=1,
        max_length=255,
    )

    description: str = Field(
        default="",
        max_length=2000,
    )

    duration_minutes: int = Field(
        ge=1,
        le=1440,
    )

    distance_km: float | None = Field(
        default=None,
        ge=0,
    )

    elevation_gain_m: float | None = Field(
        default=None,
        ge=0,
    )

    intensity: str = Field(
        default="",
        max_length=100,
    )

    heart_rate_zone: str | None = Field(
        default=None,
        max_length=100,
    )

    status: str = Field(
        default="completed",
        pattern="^(planned|completed|skipped)$",
    )

    activity_id: UUID | None = None

class TrainingSessionResponse(BaseModel):
    id: UUID
    date: date
    type: str
    title: str
    sport_type: str
    description: str
    duration_minutes: int
    distance_km: float | None
    elevation_gain_m: float | None
    intensity: str
    heart_rate_zone: str | None
    status: str
    activity_id: UUID | None


class TrainingSessionStatusUpdate(BaseModel):
    status: str = Field(
        pattern="^(planned|completed|skipped)$",
    )


class TrainingSessionActivityUpdate(BaseModel):
    activity_id: UUID | None


class TrainingActivityCandidateResponse(BaseModel):
    id: UUID
    provider: str
    provider_activity_id: str
    name: str
    sport_type: str
    start_at_local: str | None
    moving_time_seconds: int | None
    distance_m: float | None
    elevation_gain_m: float | None
    feel: int | None

    match_score: float
    best_match: bool

    sport_matches: bool

    sport_score: float
    distance_score: float | None
    duration_score: float | None
    elevation_score: float | None

class TrainingAvailableActivityResponse(BaseModel):
    id: UUID
    provider: str
    provider_activity_id: str
    name: str
    sport_type: str

    start_at_local: str | None = None

    moving_time_seconds: int | None = None
    distance_m: float | None = None
    elevation_gain_m: float | None = None

    training_load: float | None = None
    feel: int | None = None
