from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field


class TrainingSessionResponse(BaseModel):
    id: UUID
    date: date
    type: str
    title: str
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
