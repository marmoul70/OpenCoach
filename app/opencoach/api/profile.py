from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from opencoach.schemas.profile import AthleteProfileSchema
from opencoach.database.repositories import (
    ProfileRepositoryError,
    SqlProfileRepository,
)
from opencoach.database.session import get_db
from opencoach.models import (
    AthleteBody,
    AthleteEquipment,
    AthleteIdentity,
    AthleteLocation,
    AthleteNutrition,
    AthletePhysiology,
    AthleteProfile,
    AthleteTraining,
    Bike,
    Shoe,
    Watch,
)
from opencoach.services import ProfileService


router = APIRouter(
    prefix="/api/profile",
    tags=["profile"],
)

def _raise_profile_storage_unavailable(
    exc: ProfileRepositoryError,
) -> None:
    raise HTTPException(
        status_code=503,
        detail="Le stockage du profil est temporairement indisponible.",
    ) from exc

def get_profile_service(
    db: Session = Depends(get_db),
) -> ProfileService:
    repository = SqlProfileRepository(db)

    return ProfileService(repository)

def schema_to_domain(
    profile: AthleteProfileSchema,
) -> AthleteProfile:
    return AthleteProfile(
        identity=AthleteIdentity(
            first_name=profile.identity.first_name,
            last_name=profile.identity.last_name,
            birth_date=profile.identity.birth_date,
            gender=profile.identity.gender,
            avatar=profile.identity.avatar,
        ),
        body=AthleteBody(
            height_cm=profile.body.height_cm,
            weight_kg=profile.body.weight_kg,
        ),
        physiology=AthletePhysiology(
            max_heart_rate=profile.physiology.max_heart_rate,
            resting_heart_rate=profile.physiology.resting_heart_rate,
            vma=profile.physiology.vma,
            threshold_heart_rate_1=(
                profile.physiology.threshold_heart_rate_1
            ),
            threshold_heart_rate_2=(
                profile.physiology.threshold_heart_rate_2
            ),
        ),
        training=AthleteTraining(
            weekly_sessions=profile.training.weekly_sessions,
            weekly_duration_minutes=(
                profile.training.weekly_duration_minutes
            ),
            weekly_distance_km=profile.training.weekly_distance_km,
            available_days=list(profile.training.available_days),
            fatigue_threshold=profile.training.fatigue_threshold,
            experience=profile.training.experience,
            sport_disciplines=list(
                profile.training.sport_disciplines
            ),
        ),
        location=AthleteLocation(
            name=profile.location.name,
            latitude=profile.location.latitude,
            longitude=profile.location.longitude,
        ),
        equipment=AthleteEquipment(
            shoes=[
                Shoe(
                    id=shoe.id,
                    model=shoe.model,
                    brand=shoe.brand,
                    active=shoe.active,
                    distance_km=shoe.distance_km,
                    max_distance_km=shoe.max_distance_km,
                )
                for shoe in profile.equipment.shoes
            ],
            bikes=[
                Bike(
                    id=bike.id,
                    model=bike.model,
                    brand=bike.brand,
                    active=bike.active,
                    distance_km=bike.distance_km,
                )
                for bike in profile.equipment.bikes
            ],
            watches=[
                Watch(
                    id=watch.id,
                    model=watch.model,
                    brand=watch.brand,
                    active=watch.active,
                )
                for watch in profile.equipment.watches
            ],
        ),
        nutrition=AthleteNutrition(
            carbohydrates_per_hour=(
                profile.nutrition.carbohydrates_per_hour
            ),
            fluids_per_hour=profile.nutrition.fluids_per_hour,
            sodium_per_hour=profile.nutrition.sodium_per_hour,
        ),
    )


@router.get("")
def get_profile(
    service: ProfileService = Depends(get_profile_service),
) -> AthleteProfile:
    try:
        return service.get_profile()
    except ProfileRepositoryError as exc:
        _raise_profile_storage_unavailable(exc)

@router.put("")
def update_profile(
    profile: AthleteProfileSchema,
    service: ProfileService = Depends(get_profile_service),
) -> AthleteProfile:
    domain_profile = schema_to_domain(profile)

    try:
        return service.update_profile(domain_profile)
    except ProfileRepositoryError as exc:
        _raise_profile_storage_unavailable(exc)


@router.post("/reset")
def reset_profile(
    service: ProfileService = Depends(get_profile_service),
) -> AthleteProfile:
    try:
        return service.reset_profile()
    except ProfileRepositoryError as exc:
        _raise_profile_storage_unavailable(exc)
