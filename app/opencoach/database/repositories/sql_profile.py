from sqlalchemy import select
from sqlalchemy.orm import Session
from datetime import date

from opencoach.database.models import AthleteProfile as AthleteProfileModel
from opencoach.database.models import User
from opencoach.models import (
    AthleteBody,
    AthleteEquipment,
    AthleteIdentity,
    AthleteLocation,
    AthleteNutrition,
    AthletePhysiology,
    AthleteProfile,
    AthleteTraining,
)
from opencoach.database.repositories.profile import ProfileRepository

class SqlProfileRepository(ProfileRepository):
    """Persiste le profil sportif dans la base SQL."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_profile(self) -> AthleteProfile:
        profile = self._get_database_profile()

        if profile is None:
            return self.reset_profile()

        return self._to_domain(profile)

    def save_profile(self, profile: AthleteProfile) -> None:
        database_profile = self._get_database_profile()

        if database_profile is None:
            user = User(
                email=self._default_email(profile),
            )

            database_profile = AthleteProfileModel(
                user=user,
                first_name=profile.identity.first_name,
                last_name=profile.identity.last_name,
                birth_date=self._birth_date_to_database(profile.identity.birth_date),
                gender=profile.identity.gender,
                avatar_url=profile.identity.avatar,
            )

            self.session.add(database_profile)
        else:
            database_profile.first_name = profile.identity.first_name
            database_profile.last_name = profile.identity.last_name
            database_profile.birth_date = self._birth_date_to_database(
                profile.identity.birth_date
            )
            database_profile.gender = profile.identity.gender
            database_profile.avatar_url = profile.identity.avatar

        self.session.commit()
        self.session.refresh(database_profile)

    def reset_profile(self) -> AthleteProfile:
        profile = AthleteProfile()
        self.save_profile(profile)
        return profile

    def _get_database_profile(self) -> AthleteProfileModel | None:
        statement = (
            select(AthleteProfileModel)
            .join(AthleteProfileModel.user)
            .order_by(AthleteProfileModel.created_at)
            .limit(1)
        )

        return self.session.scalar(statement)

    @staticmethod
    def _default_email(profile: AthleteProfile) -> str:
        if profile.identity.first_name:
            return (
                f"{profile.identity.first_name.lower()}"
                "@opencoach.local"
            )

        return "default@opencoach.local"

    @staticmethod
    def _birth_date_to_domain(value):
        if value is None:
            return ""

        return value.isoformat()

    @staticmethod
    def _to_domain(
        profile: AthleteProfileModel,
    ) -> AthleteProfile:
        return AthleteProfile(
            identity=AthleteIdentity(
                first_name=profile.first_name,
                last_name=profile.last_name,
                birth_date=SqlProfileRepository._birth_date_to_domain(profile.birth_date),
                gender=profile.gender,
                avatar=profile.avatar_url,
            ),
            body=AthleteBody(),
            physiology=AthletePhysiology(),
            training=AthleteTraining(),
            location=AthleteLocation(),
            equipment=AthleteEquipment(
                shoes=[],
                bikes=[],
                watches=[],
            ),
            nutrition=AthleteNutrition(),
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