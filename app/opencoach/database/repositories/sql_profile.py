from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from opencoach.database.models import (
    AthleteProfile as AthleteProfileModel,
    Bike as BikeModel,
    Shoe as ShoeModel,
    User,
    Watch as WatchModel,
)
from opencoach.database.repositories.profile import ProfileRepository
from opencoach.database.repositories.errors import ProfileRepositoryError

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

LOCAL_USER_EMAIL = "local@opencoach.local"

class SqlProfileRepository(ProfileRepository):
    """Persiste le profil sportif dans la base SQL."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_profile(self) -> AthleteProfile:
        try:
            profile = self._get_database_profile()

            if profile is None:
                return self.reset_profile()

            return self._to_domain(profile)
        except ProfileRepositoryError:
            raise
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise ProfileRepositoryError(
                "Impossible de charger le profil."
            ) from exc

    def save_profile(self, profile: AthleteProfile) -> None:
        try:
            database_profile = self._get_database_profile()

            if database_profile is None:
                user = User(
                    email=LOCAL_USER_EMAIL,
                )

                database_profile = AthleteProfileModel(
                    user=user,
                )

                self.session.add(database_profile)
                self.session.flush()

            # Identité
            database_profile.first_name = profile.identity.first_name
            database_profile.last_name = profile.identity.last_name
            database_profile.birth_date = self._birth_date_to_database(
                profile.identity.birth_date
            )
            database_profile.gender = profile.identity.gender
            database_profile.avatar_url = profile.identity.avatar

            # Physique
            database_profile.height_cm = profile.body.height_cm
            database_profile.weight_kg = profile.body.weight_kg

            # Physiologie
            database_profile.max_heart_rate = (
                profile.physiology.max_heart_rate
            )
            database_profile.resting_heart_rate = (
                profile.physiology.resting_heart_rate
            )
            database_profile.vma = profile.physiology.vma
            database_profile.threshold_heart_rate_1 = (
                profile.physiology.threshold_heart_rate_1
            )
            database_profile.threshold_heart_rate_2 = (
                profile.physiology.threshold_heart_rate_2
            )

            # Entraînement
            database_profile.weekly_sessions = (
                profile.training.weekly_sessions
            )
            database_profile.weekly_duration_minutes = (
                profile.training.weekly_duration_minutes
            )
            database_profile.weekly_distance_km = (
                profile.training.weekly_distance_km
            )
            database_profile.available_days = list(
                profile.training.available_days
            )
            database_profile.fatigue_threshold = (
                profile.training.fatigue_threshold
            )
            database_profile.experience = profile.training.experience

            # Localisation
            database_profile.location_name = profile.location.name
            database_profile.latitude = profile.location.latitude
            database_profile.longitude = profile.location.longitude

            # Nutrition
            database_profile.carbohydrates_per_hour = (
                profile.nutrition.carbohydrates_per_hour
            )
            database_profile.fluids_per_hour = (
                profile.nutrition.fluids_per_hour
            )
            database_profile.sodium_per_hour = (
                profile.nutrition.sodium_per_hour
            )

            # Équipements
            database_profile.shoes.clear()
            database_profile.bikes.clear()
            database_profile.watches.clear()

            database_profile.shoes.extend(
                ShoeModel(
                    id=shoe.id,
                    model=shoe.model,
                    brand=shoe.brand,
                    active=shoe.active,
                    distance_km=shoe.distance_km,
                    max_distance_km=shoe.max_distance_km,
                )
                for shoe in profile.equipment.shoes
            )

            database_profile.bikes.extend(
                BikeModel(
                    id=bike.id,
                    model=bike.model,
                    brand=bike.brand,
                    active=bike.active,
                    distance_km=bike.distance_km,
                )
                for bike in profile.equipment.bikes
            )

            database_profile.watches.extend(
                WatchModel(
                    id=watch.id,
                    model=watch.model,
                    brand=watch.brand,
                    active=watch.active,
                )
                for watch in profile.equipment.watches
            )

            self.session.commit()
            self.session.refresh(database_profile)

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise ProfileRepositoryError(
                "Impossible d'enregistrer le profil."
            ) from exc

    def reset_profile(self) -> AthleteProfile:
        profile = AthleteProfile()
        self.save_profile(profile)
        return profile

    def _get_database_profile(self) -> AthleteProfileModel | None:
        statement = (
            select(AthleteProfileModel)
            .join(AthleteProfileModel.user)
            .where(User.email == LOCAL_USER_EMAIL)
        )

        return self.session.scalar(statement)

    @staticmethod
    def _to_domain(
        profile: AthleteProfileModel,
    ) -> AthleteProfile:
        return AthleteProfile(
            identity=AthleteIdentity(
                first_name=profile.first_name,
                last_name=profile.last_name,
                birth_date=SqlProfileRepository._birth_date_to_domain(
                    profile.birth_date
                ),
                gender=profile.gender,
                avatar=profile.avatar_url,
            ),
            body=AthleteBody(
                height_cm=profile.height_cm,
                weight_kg=profile.weight_kg,
            ),
            physiology=AthletePhysiology(
                max_heart_rate=profile.max_heart_rate,
                resting_heart_rate=profile.resting_heart_rate,
                vma=profile.vma,
                threshold_heart_rate_1=profile.threshold_heart_rate_1,
                threshold_heart_rate_2=profile.threshold_heart_rate_2,
            ),
            training=AthleteTraining(
                weekly_sessions=profile.weekly_sessions,
                weekly_duration_minutes=profile.weekly_duration_minutes,
                weekly_distance_km=profile.weekly_distance_km,
                available_days=list(profile.available_days or []),
                fatigue_threshold=profile.fatigue_threshold,
                experience=profile.experience,
            ),
            location=AthleteLocation(
                name=profile.location_name,
                latitude=profile.latitude,
                longitude=profile.longitude,
            ),
            equipment=AthleteEquipment(
                shoes=[
                    Shoe(
                        id=str(shoe.id),
                        model=shoe.model,
                        brand=shoe.brand,
                        active=shoe.active,
                        distance_km=shoe.distance_km,
                        max_distance_km=shoe.max_distance_km,
                    )
                    for shoe in profile.shoes
                ],
                bikes=[
                    Bike(
                        id=str(bike.id),
                        model=bike.model,
                        brand=bike.brand,
                        active=bike.active,
                        distance_km=bike.distance_km,
                    )
                    for bike in profile.bikes
                ],
                watches=[
                    Watch(
                        id=str(watch.id),
                        model=watch.model,
                        brand=watch.brand,
                        active=watch.active,
                    )
                    for watch in profile.watches
                ],
            ),
            nutrition=AthleteNutrition(
                carbohydrates_per_hour=profile.carbohydrates_per_hour,
                fluids_per_hour=profile.fluids_per_hour,
                sodium_per_hour=profile.sodium_per_hour,
            ),
        )

    @staticmethod
    def _birth_date_to_database(value: str) -> date | None:
        if not value:
            return None

        return date.fromisoformat(value)

    @staticmethod
    def _birth_date_to_domain(value: date | None) -> str:
        if value is None:
            return ""

        return value.isoformat()
