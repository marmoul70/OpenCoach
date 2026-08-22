from dataclasses import dataclass
from typing import Literal, TypeAlias


ComparisonOperator = Literal[
    "lt",
    "lte",
    "gt",
    "gte",
    "between",
]


@dataclass(frozen=True)
class RelativeLoadLimitParameters:
    """Limite relative appliquée à une référence de charge."""

    reference: Literal[
        "baseline",
        "previous_week",
        "recent_average",
    ]

    max_multiplier: float

    def __post_init__(self) -> None:
        if self.max_multiplier <= 0:
            raise ValueError(
                "Le multiplicateur de charge doit être positif."
            )


@dataclass(frozen=True)
class AbsoluteLoadLimitParameters:
    """Limite absolue appliquée à une métrique de charge."""

    metric: Literal[
        "training_load",
        "duration_minutes",
        "distance_km",
        "elevation_gain_m",
    ]

    operator: ComparisonOperator

    value: float
    upper_value: float | None = None

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError(
                "La valeur limite ne peut pas être négative."
            )

        if self.operator == "between":
            if self.upper_value is None:
                raise ValueError(
                    "Une comparaison 'between' nécessite "
                    "une borne supérieure."
                )

            if self.upper_value < self.value:
                raise ValueError(
                    "La borne supérieure doit être supérieure "
                    "ou égale à la borne inférieure."
                )

        elif self.upper_value is not None:
            raise ValueError(
                "Une borne supérieure n'est autorisée "
                "qu'avec l'opérateur 'between'."
            )


@dataclass(frozen=True)
class RecoverySpacingParameters:
    """Politique de fréquence des périodes de récupération."""

    max_build_weeks_before_recovery: int

    minimum_recovery_days: int

    def __post_init__(self) -> None:
        if self.max_build_weeks_before_recovery < 1:
            raise ValueError(
                "Le nombre de semaines de build doit être positif."
            )

        if self.minimum_recovery_days < 1:
            raise ValueError(
                "La récupération minimale doit être positive."
            )


@dataclass(frozen=True)
class TaperParameters:
    """Enveloppe adaptable d'une politique d'affûtage."""

    minimum_days: int
    maximum_days: int

    minimum_load_ratio: float
    maximum_load_ratio: float

    def __post_init__(self) -> None:
        if self.minimum_days < 1:
            raise ValueError(
                "La durée minimale d'affûtage doit être positive."
            )

        if self.maximum_days < self.minimum_days:
            raise ValueError(
                "La durée maximale d'affûtage ne peut pas être "
                "inférieure à la durée minimale."
            )

        if not (
            0 < self.minimum_load_ratio <= 1
        ):
            raise ValueError(
                "Le ratio minimal de charge doit être compris "
                "entre 0 et 1."
            )

        if not (
            0 < self.maximum_load_ratio <= 1
        ):
            raise ValueError(
                "Le ratio maximal de charge doit être compris "
                "entre 0 et 1."
            )

        if (
            self.minimum_load_ratio
            > self.maximum_load_ratio
        ):
            raise ValueError(
                "Le ratio minimal ne peut pas dépasser "
                "le ratio maximal."
            )


@dataclass(frozen=True)
class RaceProximityParameters:
    """Protection d'une période située avant une compétition."""

    days_before_race: int

    prohibited_phase_types: tuple[
        str,
        ...
    ] = ()

    def __post_init__(self) -> None:
        if self.days_before_race < 0:
            raise ValueError(
                "La proximité de course ne peut pas être négative."
            )


@dataclass(frozen=True)
class AssessmentTimingParameters:
    """Contraintes temporelles autour d'une évaluation physiologique."""

    minimum_days_before_primary_race: int

    minimum_days_between_assessments: int

    def __post_init__(self) -> None:
        if self.minimum_days_before_primary_race < 0:
            raise ValueError(
                "Le délai avant course ne peut pas être négatif."
            )

        if self.minimum_days_between_assessments < 0:
            raise ValueError(
                "Le délai entre évaluations ne peut pas être négatif."
            )


PolicyParameters: TypeAlias = (
    RelativeLoadLimitParameters
    | AbsoluteLoadLimitParameters
    | RecoverySpacingParameters
    | TaperParameters
    | RaceProximityParameters
    | AssessmentTimingParameters
)
