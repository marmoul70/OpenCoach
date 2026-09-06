from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from opencoach.database.models import (
    ActivityEquipmentAssignment,
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
    HeartRateZone,
    HeartRateZones,
    AthleteNutrition,
    AthletePhysiology,
    AthleteProfile,
    AthleteTraining,
    Bike,
    Shoe,
    Watch,
)

class SqlProfileRepository(ProfileRepository):
    """Persiste le profil sportif dans la base SQL."""

    def __init__(
        self,
        session: Session,
        user_id: UUID,
    ) -> None:
        self.session = session
        self.user_id = user_id

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
                user = self.session.scalar(
                    select(User)
                    .where(
                        User.id
                        == self.user_id
                    )
                )

                if user is None:
                    raise ProfileRepositoryError(
                        "Utilisateur OpenCoach introuvable."
                    )

                database_profile = AthleteProfileModel(
                    user=user,
                )

                self.session.add(
                    database_profile
                )

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
            database_profile.heart_rate_zones = (
                self._heart_rate_zones_to_database(
                    profile.physiology.heart_rate_zones
                )
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
            database_profile.sport_disciplines = list(
                profile.training.sport_disciplines
            )

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
            #
            # Les équipements sont synchronisés par identifiant.
            # Un objet existant ne doit jamais être supprimé puis
            # recréé lors d'une simple sauvegarde du profil :
            # les affectations d'activités référencent directement
            # les identifiants des chaussures et des vélos.
            self._sync_shoes(
                database_profile,
                profile.equipment.shoes,
            )
            self._sync_bikes(
                database_profile,
                profile.equipment.bikes,
            )
            self._sync_watches(
                database_profile,
                profile.equipment.watches,
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

    def _get_database_profile(
        self,
    ) -> AthleteProfileModel | None:
        statement = (
            select(
                AthleteProfileModel
            )
            .where(
                AthleteProfileModel.user_id
                == self.user_id
            )
        )

        return self.session.scalar(
            statement
        )

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
                heart_rate_zones=(
                    SqlProfileRepository
                    ._heart_rate_zones_to_domain(
                        profile.heart_rate_zones
                    )
                ),
            ),
            training=AthleteTraining(
                weekly_sessions=profile.weekly_sessions,
                weekly_duration_minutes=profile.weekly_duration_minutes,
                weekly_distance_km=profile.weekly_distance_km,
                available_days=list(profile.available_days or []),
                fatigue_threshold=profile.fatigue_threshold,
                experience=profile.experience,
                sport_disciplines=list(
                    profile.sport_disciplines
                    or []
                ),
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
                        category=shoe.category,
                        preferred=shoe.preferred,
                        distance_km=shoe.distance_km,
                        warning_distance_km=shoe.warning_distance_km,
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
                        category=bike.category,
                        preferred=bike.preferred,
                        distance_km=bike.distance_km,
                        maintenance_distance_km=bike.maintenance_distance_km,
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

    def _sync_shoes(
        self,
        database_profile: AthleteProfileModel,
        shoes: list[Shoe],
    ) -> None:
        existing_by_id = {
            str(shoe.id): shoe
            for shoe in database_profile.shoes
        }
        incoming_ids = {
            str(shoe.id)
            for shoe in shoes
        }

        for database_shoe in list(
            database_profile.shoes
        ):
            if (
                str(database_shoe.id)
                in incoming_ids
            ):
                continue

            has_history = (
                self.session.scalar(
                    select(
                        ActivityEquipmentAssignment.id
                    )
                    .where(
                        ActivityEquipmentAssignment
                        .athlete_profile_id
                        == database_profile.id,
                        ActivityEquipmentAssignment
                        .shoe_id
                        == database_shoe.id,
                    )
                    .limit(1)
                )
                is not None
            )

            if has_history:
                # Une paire déjà utilisée fait partie
                # de l'historique sportif de l'athlète.
                database_shoe.active = False
                database_shoe.preferred = False
            else:
                database_profile.shoes.remove(
                    database_shoe
                )

        for shoe in shoes:
            database_shoe = existing_by_id.get(
                str(shoe.id)
            )

            if database_shoe is None:
                database_shoe = ShoeModel(
                    id=shoe.id,
                )
                database_profile.shoes.append(
                    database_shoe
                )

            database_shoe.model = shoe.model
            database_shoe.brand = shoe.brand
            database_shoe.active = shoe.active
            database_shoe.category = shoe.category
            database_shoe.preferred = shoe.preferred
            database_shoe.distance_km = (
                shoe.distance_km
            )
            database_shoe.warning_distance_km = (
                shoe.warning_distance_km
            )
            database_shoe.max_distance_km = (
                shoe.max_distance_km
            )


    def _sync_bikes(
        self,
        database_profile: AthleteProfileModel,
        bikes: list[Bike],
    ) -> None:
        existing_by_id = {
            str(bike.id): bike
            for bike in database_profile.bikes
        }
        incoming_ids = {
            str(bike.id)
            for bike in bikes
        }

        for database_bike in list(
            database_profile.bikes
        ):
            if (
                str(database_bike.id)
                in incoming_ids
            ):
                continue

            has_history = (
                self.session.scalar(
                    select(
                        ActivityEquipmentAssignment.id
                    )
                    .where(
                        ActivityEquipmentAssignment
                        .athlete_profile_id
                        == database_profile.id,
                        ActivityEquipmentAssignment
                        .bike_id
                        == database_bike.id,
                    )
                    .limit(1)
                )
                is not None
            )

            if has_history:
                # Même règle pour les vélos :
                # l'historique d'utilisation est conservé.
                database_bike.active = False
                database_bike.preferred = False
            else:
                database_profile.bikes.remove(
                    database_bike
                )

        for bike in bikes:
            database_bike = existing_by_id.get(
                str(bike.id)
            )

            if database_bike is None:
                database_bike = BikeModel(
                    id=bike.id,
                )
                database_profile.bikes.append(
                    database_bike
                )

            database_bike.model = bike.model
            database_bike.brand = bike.brand
            database_bike.active = bike.active
            database_bike.category = bike.category
            database_bike.preferred = bike.preferred
            database_bike.distance_km = (
                bike.distance_km
            )
            database_bike.maintenance_distance_km = (
                bike.maintenance_distance_km
            )


    @staticmethod
    def _sync_watches(
        database_profile: AthleteProfileModel,
        watches: list[Watch],
    ) -> None:
        existing_by_id = {
            str(watch.id): watch
            for watch in database_profile.watches
        }
        incoming_ids = {
            str(watch.id)
            for watch in watches
        }

        for watch in list(database_profile.watches):
            if str(watch.id) not in incoming_ids:
                database_profile.watches.remove(
                    watch
                )

        for watch in watches:
            database_watch = existing_by_id.get(
                str(watch.id)
            )

            if database_watch is None:
                database_watch = WatchModel(
                    id=watch.id,
                )
                database_profile.watches.append(
                    database_watch
                )

            database_watch.model = watch.model
            database_watch.brand = watch.brand
            database_watch.active = watch.active

    @staticmethod
    def _heart_rate_zones_to_database(
        zones: HeartRateZones,
    ) -> dict[str, dict[str, int]]:
        result: dict[str, dict[str, int]] = {}

        for name in (
            "z1",
            "z2",
            "z3",
            "z4",
            "z5",
        ):
            zone = getattr(
                zones,
                name,
            )

            if zone is not None:
                result[name] = {
                    "max_bpm": zone.max_bpm,
                }

        return result

    @staticmethod
    def _heart_rate_zones_to_domain(
        data: dict[str, dict[str, int]] | None,
    ) -> HeartRateZones:
        data = data or {}

        def load_zone(
            name: str,
        ) -> HeartRateZone | None:
            raw = data.get(name)

            if not raw:
                return None

            max_bpm = raw.get(
                "max_bpm",
            )

            if max_bpm is None:
                return None

            return HeartRateZone(
                max_bpm=int(
                    max_bpm,
                ),
            )

        return HeartRateZones(
            z1=load_zone("z1"),
            z2=load_zone("z2"),
            z3=load_zone("z3"),
            z4=load_zone("z4"),
            z5=load_zone("z5"),
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
