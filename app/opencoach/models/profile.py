from dataclasses import dataclass, field
from typing import Literal


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


@dataclass
class AthleteIdentity:
    first_name: str = ""
    last_name: str = ""
    birth_date: str = ""
    gender: Gender = "unspecified"
    avatar: str | None = None


@dataclass
class AthleteBody:
    height_cm: float | None = None
    weight_kg: float | None = None


@dataclass
class HeartRateZone:
    max_bpm: int


@dataclass
class HeartRateZones:
    z1: HeartRateZone | None = None
    z2: HeartRateZone | None = None
    z3: HeartRateZone | None = None
    z4: HeartRateZone | None = None
    z5: HeartRateZone | None = None


@dataclass
class AthletePhysiology:
    max_heart_rate: int | None = None
    resting_heart_rate: int | None = None
    vma: float | None = None
    threshold_heart_rate_1: int | None = None
    threshold_heart_rate_2: int | None = None
    heart_rate_zones: HeartRateZones = field(
        default_factory=HeartRateZones,
    )


@dataclass
class AthleteTraining:
    weekly_sessions: int | None = None
    weekly_duration_minutes: int | None = None
    weekly_distance_km: float | None = None
    available_days: list[int] = field(default_factory=list)
    fatigue_threshold: float | None = None
    experience: Experience = "beginner"
    sport_disciplines: list[
        SportDiscipline
    ] = field(
        default_factory=list
    )


@dataclass
class AthleteLocation:
    name: str | None = None
    latitude: float | None = None
    longitude: float | None = None


@dataclass
class EquipmentItem:
    id: str
    model: str
    brand: str | None = None
    active: bool = True


@dataclass
class Shoe(EquipmentItem):
    distance_km: float = 0
    max_distance_km: float | None = None


@dataclass
class Bike(EquipmentItem):
    distance_km: float = 0


@dataclass
class Watch(EquipmentItem):
    pass


@dataclass
class AthleteEquipment:
    shoes: list[Shoe] = field(default_factory=list)
    bikes: list[Bike] = field(default_factory=list)
    watches: list[Watch] = field(default_factory=list)


@dataclass
class AthleteNutrition:
    carbohydrates_per_hour: float | None = None
    fluids_per_hour: float | None = None
    sodium_per_hour: float | None = None


@dataclass
class AthleteProfile:
    identity: AthleteIdentity = field(
        default_factory=AthleteIdentity,
    )
    body: AthleteBody = field(
        default_factory=AthleteBody,
    )
    physiology: AthletePhysiology = field(
        default_factory=AthletePhysiology,
    )
    training: AthleteTraining = field(
        default_factory=AthleteTraining,
    )
    location: AthleteLocation = field(
        default_factory=AthleteLocation,
    )
    equipment: AthleteEquipment = field(
        default_factory=AthleteEquipment,
    )
    nutrition: AthleteNutrition = field(
        default_factory=AthleteNutrition,
    )
