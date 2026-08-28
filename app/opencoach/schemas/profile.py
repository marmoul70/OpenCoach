from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


Gender = Literal["male", "female", "other", "unspecified"]

Experience = Literal[
    "beginner",
    "intermediate",
    "advanced",
    "expert",
]


SportDiscipline = Literal[
    "road_running",
    "trail_running",
]


class AthleteIdentitySchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    first_name: str = Field(default="", max_length=100)
    last_name: str = Field(default="", max_length=100)
    birth_date: str = ""
    gender: Gender = "unspecified"
    avatar: str | None = None

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return value.strip()

    @field_validator("birth_date")
    @classmethod
    def validate_birth_date(cls, value: str) -> str:
        if not value:
            return value

        try:
            parsed = date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError(
                "La date de naissance doit être au format YYYY-MM-DD."
            ) from exc

        if parsed > date.today():
            raise ValueError(
                "La date de naissance ne peut pas être dans le futur."
            )

        return value


class AthleteBodySchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    height_cm: float | None = Field(default=None, gt=0, le=250)
    weight_kg: float | None = Field(default=None, gt=0, le=500)


class AthletePhysiologySchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_heart_rate: int | None = Field(default=None, gt=0, le=250)
    resting_heart_rate: int | None = Field(default=None, gt=0, le=150)
    vma: float | None = Field(default=None, gt=0, le=40)
    threshold_heart_rate_1: int | None = Field(default=None, gt=0, le=250)
    threshold_heart_rate_2: int | None = Field(default=None, gt=0, le=250)

    @model_validator(mode="after")
    def validate_thresholds(self) -> "AthletePhysiologySchema":
        if (
            self.resting_heart_rate is not None
            and self.max_heart_rate is not None
            and self.resting_heart_rate >= self.max_heart_rate
        ):
            raise ValueError(
                "La FC au repos doit être inférieure à la FC maximale."
            )

        if (
            self.resting_heart_rate is not None
            and self.threshold_heart_rate_1 is not None
            and self.resting_heart_rate >= self.threshold_heart_rate_1
        ):
            raise ValueError(
                "La FC au repos doit être inférieure à SV1."
            )

        if (
            self.threshold_heart_rate_1 is not None
            and self.threshold_heart_rate_2 is not None
            and self.threshold_heart_rate_1 >= self.threshold_heart_rate_2
        ):
            raise ValueError("SV1 doit être inférieur à SV2.")

        if (
            self.threshold_heart_rate_2 is not None
            and self.max_heart_rate is not None
            and self.threshold_heart_rate_2 >= self.max_heart_rate
        ):
            raise ValueError(
                "SV2 doit être inférieur à la FC maximale."
            )

        return self


class AthleteTrainingSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    weekly_sessions: int | None = Field(default=None, ge=0)
    weekly_duration_minutes: int | None = Field(default=None, ge=0)
    weekly_distance_km: float | None = Field(default=None, ge=0)
    available_days: list[int] = Field(default_factory=list)
    fatigue_threshold: float | None = Field(default=None, ge=0)
    experience: Experience = "beginner"
    sport_disciplines: list[
        SportDiscipline
    ] = Field(
        default_factory=list
    )

    @field_validator("sport_disciplines")
    @classmethod
    def validate_sport_disciplines(
        cls,
        value: list[SportDiscipline],
    ) -> list[SportDiscipline]:
        if len(value) != len(set(value)):
            raise ValueError(
                "Les disciplines sportives "
                "ne peuvent pas être dupliquées."
            )

        return value


    @field_validator("available_days")
    @classmethod
    def validate_available_days(cls, value: list[int]) -> list[int]:
        if any(day < 0 or day > 6 for day in value):
            raise ValueError(
                "Les jours disponibles doivent être compris entre 0 et 6."
            )

        if len(value) != len(set(value)):
            raise ValueError(
                "Les jours disponibles ne peuvent pas être dupliqués."
            )

        return sorted(value)


class AthleteLocationSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class EquipmentItemSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=100)
    model: str = Field(min_length=1, max_length=200)
    brand: str | None = Field(default=None, max_length=100)
    active: bool = True


class ShoeSchema(EquipmentItemSchema):
    distance_km: float = Field(default=0, ge=0)
    max_distance_km: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_max_distance(self) -> "ShoeSchema":
        if (
            self.max_distance_km is not None
            and self.max_distance_km < self.distance_km
        ):
            raise ValueError(
                "La distance maximale doit être supérieure ou égale "
                "à la distance parcourue."
            )

        return self


class BikeSchema(EquipmentItemSchema):
    distance_km: float = Field(default=0, ge=0)


class WatchSchema(EquipmentItemSchema):
    pass


class AthleteEquipmentSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    shoes: list[ShoeSchema] = Field(default_factory=list)
    bikes: list[BikeSchema] = Field(default_factory=list)
    watches: list[WatchSchema] = Field(default_factory=list)


class AthleteNutritionSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    carbohydrates_per_hour: float | None = Field(default=None, ge=0)
    fluids_per_hour: float | None = Field(default=None, ge=0)
    sodium_per_hour: float | None = Field(default=None, ge=0)


class AthleteProfileSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    identity: AthleteIdentitySchema = Field(
        default_factory=AthleteIdentitySchema,
    )
    body: AthleteBodySchema = Field(
        default_factory=AthleteBodySchema,
    )
    physiology: AthletePhysiologySchema = Field(
        default_factory=AthletePhysiologySchema,
    )
    training: AthleteTrainingSchema = Field(
        default_factory=AthleteTrainingSchema,
    )
    location: AthleteLocationSchema = Field(
        default_factory=AthleteLocationSchema,
    )
    equipment: AthleteEquipmentSchema = Field(
        default_factory=AthleteEquipmentSchema,
    )
    nutrition: AthleteNutritionSchema = Field(
        default_factory=AthleteNutritionSchema,
    )
