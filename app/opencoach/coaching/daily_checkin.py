"""Check-in quotidien déclaratif de l'athlète.

Le check-in décrit l'état subjectif de l'athlète.

Il ne modifie jamais directement une séance.

Convention utilisateur :

- energy_rating :
    5 = excellente forme / très frais
    1 = épuisé

- pain_wellness_rating :
    5 = aucune douleur
    1 = douleur / gêne très importante

L'interprétation et les éventuelles propositions d'adaptation
appartiennent à une politique de coaching séparée.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from uuid import UUID


class PainArea(StrEnum):
    """Zone anatomique déclarée par l'athlète."""

    HEAD = "head"
    NECK = "neck"
    SHOULDER = "shoulder"

    BACK = "back"
    LOWER_BACK = "lower_back"

    HIP = "hip"
    GROIN = "groin"

    THIGH = "thigh"
    KNEE = "knee"

    CALF = "calf"
    SHIN = "shin"

    ANKLE = "ankle"
    ACHILLES = "achilles"
    FOOT = "foot"

    OTHER = "other"


class BodySide(StrEnum):
    """Latéralité d'une gêne ou douleur."""

    LEFT = "left"
    RIGHT = "right"
    BOTH = "both"
    CENTER = "center"
    NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True, slots=True)
class PainLocation:
    """Localisation structurée d'une gêne."""

    area: PainArea

    side: BodySide = (
        BodySide.NOT_APPLICABLE
    )


@dataclass(frozen=True, slots=True)
class AthleteDailyCheckIn:
    """État quotidien déclaré par l'athlète."""

    date: date

    energy_rating: int
    pain_wellness_rating: int

    id: UUID | None = None

    illness: bool = False
    unavailable: bool = False

    pain_locations: tuple[
        PainLocation,
        ...
    ] = ()

    note: str | None = None

    def __post_init__(self) -> None:
        for name, value in (
            (
                "energy_rating",
                self.energy_rating,
            ),
            (
                "pain_wellness_rating",
                self.pain_wellness_rating,
            ),
        ):
            if not 1 <= value <= 5:
                raise ValueError(
                    f"{name} doit être compris "
                    "entre 1 et 5."
                )

        if (
            self.pain_wellness_rating == 5
            and self.pain_locations
        ):
            raise ValueError(
                "Une localisation de douleur ne peut "
                "pas être déclarée lorsque "
                "pain_wellness_rating vaut 5."
            )

        if (
            len(self.pain_locations)
            != len(
                set(self.pain_locations)
            )
        ):
            raise ValueError(
                "Une même localisation ne peut "
                "apparaître qu'une seule fois."
            )

        if (
            self.note is not None
            and not self.note.strip()
        ):
            raise ValueError(
                "La note ne peut pas être vide."
            )
