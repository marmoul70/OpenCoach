"""Concepts métier décrivant les stimuli d'entraînement.

Ce module décrit ce que le moteur de trajectoire demande à une semaine
d'entraînement. Il ne décrit volontairement pas le contenu concret des
séances : cette responsabilité appartient au moteur de génération des séances.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class TrainingModality(StrEnum):
    """Modalités pouvant contribuer à l'entraînement."""

    RUNNING = "running"
    TRAIL_RUNNING = "trail_running"
    CYCLING = "cycling"
    SWIMMING = "swimming"
    STRENGTH = "strength"


class TrainingStimulus(StrEnum):
    """Objectifs physiologiques ou spécifiques demandés par la trajectoire."""

    AEROBIC_EASY = "aerobic_easy"
    AEROBIC_ENDURANCE = "aerobic_endurance"

    THRESHOLD = "threshold"
    SPEED_DEVELOPMENT = "speed_development"
    VO2MAX = "vo2max"

    UPHILL_STRENGTH = "uphill_strength"
    UPHILL_STRENGTH_ENDURANCE = "uphill_strength_endurance"
    UPHILL_THRESHOLD = "uphill_threshold"
    DOWNHILL_SPECIFICITY = "downhill_specificity"

    LONG_ENDURANCE = "long_endurance"
    RACE_SPECIFIC = "race_specific"

    STRENGTH_LOWER_BODY = "strength_lower_body"
    STRENGTH_CORE = "strength_core"

    RECOVERY = "recovery"


class StimulusLoadCategory(StrEnum):
    """Nature de sollicitation d'un stimulus d'entraînement."""

    SUPPORT = "support"
    ENDURANCE = "endurance"
    QUALITY = "quality"
    STRENGTH = "strength"


def stimulus_load_category(
    stimulus: TrainingStimulus,
) -> StimulusLoadCategory:
    """Classe un stimulus selon sa nature de sollicitation."""

    if stimulus in {
        TrainingStimulus.THRESHOLD,
        TrainingStimulus.SPEED_DEVELOPMENT,
        TrainingStimulus.VO2MAX,
        TrainingStimulus.UPHILL_STRENGTH,
        TrainingStimulus.UPHILL_STRENGTH_ENDURANCE,
        TrainingStimulus.UPHILL_THRESHOLD,
        TrainingStimulus.DOWNHILL_SPECIFICITY,
        TrainingStimulus.RACE_SPECIFIC,
    }:
        return StimulusLoadCategory.QUALITY

    if stimulus in {
        TrainingStimulus.AEROBIC_ENDURANCE,
        TrainingStimulus.LONG_ENDURANCE,
    }:
        return StimulusLoadCategory.ENDURANCE

    if stimulus in {
        TrainingStimulus.STRENGTH_LOWER_BODY,
        TrainingStimulus.STRENGTH_CORE,
    }:
        return StimulusLoadCategory.STRENGTH

    return StimulusLoadCategory.SUPPORT


class SpecificityLevel(StrEnum):
    """Importance de reproduire la modalité ou le contexte cible."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class SubstitutionPolicy(StrEnum):
    """Liberté laissée au coach pour changer de modalité."""

    ALLOWED = "allowed"
    CONDITIONAL = "conditional"
    FORBIDDEN = "forbidden"


class StimulusPriority(StrEnum):
    """Importance du stimulus dans la semaine."""

    SUPPORT = "support"
    IMPORTANT = "important"
    KEY = "key"


@dataclass(frozen=True, slots=True)
class TrainingStimulusRequirement:
    """Besoin d'entraînement produit par le moteur de trajectoire.

    Il indique au moteur de génération des séances ce qui doit être obtenu sans lui imposer
    la séance concrète permettant d'y parvenir.
    """

    stimulus: TrainingStimulus
    priority: StimulusPriority
    specificity: SpecificityLevel
    substitution: SubstitutionPolicy

    preferred_modalities: tuple[TrainingModality, ...] = ()
    required_modalities: tuple[TrainingModality, ...] = ()

    duration_min_minutes: int | None = None
    duration_max_minutes: int | None = None

    def __post_init__(self) -> None:
        if (
            self.duration_min_minutes is not None
            and self.duration_min_minutes <= 0
        ):
            raise ValueError(
                "La durée minimale doit être strictement positive."
            )

        if (
            self.duration_max_minutes is not None
            and self.duration_max_minutes <= 0
        ):
            raise ValueError(
                "La durée maximale doit être strictement positive."
            )

        if (
            self.duration_min_minutes is not None
            and self.duration_max_minutes is not None
            and self.duration_min_minutes > self.duration_max_minutes
        ):
            raise ValueError(
                "La durée minimale ne peut pas dépasser "
                "la durée maximale."
            )

        if (
            self.substitution is SubstitutionPolicy.FORBIDDEN
            and not self.required_modalities
        ):
            raise ValueError(
                "Un stimulus non substituable doit définir "
                "au moins une modalité obligatoire."
            )
