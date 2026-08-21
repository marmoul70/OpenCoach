from datetime import date
from uuid import UUID

from pydantic import (
    BaseModel,
    Field,
    model_validator,
)


RACE_TYPE_PATTERN = (
    "^(trail|road|ultra|other)$"
)

RACE_PRIORITY_PATTERN = (
    "^(primary|training)$"
)

RACE_STATUS_PATTERN = (
    "^(planned|completed|abandoned|not_participated)$"
)


class RaceCreate(BaseModel):
    date: date

    name: str = Field(
        min_length=1,
        max_length=255,
    )

    location: str = Field(
        default="",
        max_length=255,
    )

    race_type: str = Field(
        pattern=RACE_TYPE_PATTERN,
    )

    priority: str = Field(
        default="training",
        pattern=RACE_PRIORITY_PATTERN,
    )

    distance_km: float = Field(
        gt=0,
    )

    elevation_gain_m: float | None = Field(
        default=None,
        ge=0,
    )

    target_time_minutes: int | None = Field(
        default=None,
        ge=1,
    )

    status: str = Field(
        default="planned",
        pattern=RACE_STATUS_PATTERN,
    )

    actual_distance_km: float | None = Field(
        default=None,
        ge=0,
    )

    actual_elevation_gain_m: float | None = Field(
        default=None,
        ge=0,
    )

    actual_time_minutes: int | None = Field(
        default=None,
        ge=0,
    )

    ranking: int | None = Field(
        default=None,
        ge=1,
    )

    notes: str = Field(
        default="",
        max_length=4000,
    )

    activity_id: UUID | None = None

    @model_validator(
        mode="after",
    )
    def validate_result(
        self,
    ):
        if (
            self.status
            == "not_participated"
        ):
            if (
                self.actual_distance_km
                not in {
                    None,
                    0,
                }
            ):
                raise ValueError(
                    (
                        "Une course non participée "
                        "ne peut pas avoir de "
                        "distance réalisée."
                    )
                )

            if (
                self.actual_elevation_gain_m
                not in {
                    None,
                    0,
                }
            ):
                raise ValueError(
                    (
                        "Une course non participée "
                        "ne peut pas avoir de "
                        "dénivelé réalisé."
                    )
                )

            if (
                self.actual_time_minutes
                not in {
                    None,
                    0,
                }
            ):
                raise ValueError(
                    (
                        "Une course non participée "
                        "ne peut pas avoir de "
                        "durée réalisée."
                    )
                )

        return self


class RaceUpdate(RaceCreate):
    pass

class RaceActualResultResponse(BaseModel):
    source: str

    activity_id: UUID | None

    distance_km: float | None
    elevation_gain_m: float | None
    duration_minutes: float | None

    training_load: float | None

class RaceResponse(BaseModel):
    id: UUID
    date: date

    name: str
    location: str

    race_type: str
    priority: str

    distance_km: float
    elevation_gain_m: float | None
    target_time_minutes: int | None

    status: str

    actual_distance_km: float | None
    actual_elevation_gain_m: float | None
    actual_time_minutes: int | None

    ranking: int | None
    notes: str

    actual_result: RaceActualResultResponse

    activity_id: UUID | None

class RaceActivityUpdate(BaseModel):
    activity_id: UUID | None


class RaceActivityCandidateResponse(BaseModel):
    id: UUID

    provider: str
    provider_activity_id: str

    name: str
    sport_type: str

    start_at_local: str | None

    moving_time_seconds: int | None

    distance_m: float | None
    elevation_gain_m: float | None

    training_load: float | None
    feel: int | None