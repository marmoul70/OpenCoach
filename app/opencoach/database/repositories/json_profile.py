import json
from dataclasses import asdict
from pathlib import Path

from opencoach.schemas.profile import AthleteProfileSchema
from opencoach.database.repositories.profile import ProfileRepository
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


class JsonProfileRepository(ProfileRepository):
    """Persist the athlete profile in a JSON file."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def get_profile(self) -> AthleteProfile:
        if not self.path.exists():
            return self.reset_profile()

        try:
            with self.path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Le fichier de profil contient un JSON invalide : {exc}"
            ) from exc

        return self._from_dict(data)

    def save_profile(self, profile: AthleteProfile) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)

        data = asdict(profile)

        # Même les données internes sont validées avant persistance.
        validated = AthleteProfileSchema.model_validate(data)

        with self.path.open("w", encoding="utf-8") as file:
            json.dump(
                validated.model_dump(),
                file,
                ensure_ascii=False,
                indent=2,
            )
            file.write("\n")

    def reset_profile(self) -> AthleteProfile:
        profile = AthleteProfile()
        self.save_profile(profile)
        return profile

    @staticmethod
    def _from_dict(data: dict) -> AthleteProfile:
        # Le JSON est une frontière externe : validation complète avant
        # conversion vers les dataclasses métier.
        validated = AthleteProfileSchema.model_validate(data)
        data = validated.model_dump()

        equipment = data["equipment"]

        return AthleteProfile(
            identity=AthleteIdentity(
                **data["identity"],
            ),
            body=AthleteBody(
                **data["body"],
            ),
            physiology=AthletePhysiology(
                **data["physiology"],
            ),
            training=AthleteTraining(
                **data["training"],
            ),
            location=AthleteLocation(
                **data["location"],
            ),
            equipment=AthleteEquipment(
                shoes=[
                    Shoe(**shoe)
                    for shoe in equipment["shoes"]
                ],
                bikes=[
                    Bike(**bike)
                    for bike in equipment["bikes"]
                ],
                watches=[
                    Watch(**watch)
                    for watch in equipment["watches"]
                ],
            ),
            nutrition=AthleteNutrition(
                **data["nutrition"],
            ),
        )
