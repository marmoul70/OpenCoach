"""Adaptations recommandées de la trajectoire d'entraînement.

Un TrajectoryAdjustment représente la réponse du moteur Python à un
événement ou à une contrainte.

Il modifie le cadre de progression, jamais le contenu concret d'une
séance. L'athlète conserve la décision finale.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .training_stimulus import (
    TrainingModality,
    TrainingStimulus,
)


class AdjustmentSeverity(StrEnum):
    """Importance de l'adaptation recommandée."""

    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"


class LoadAdjustment(StrEnum):
    """Direction recommandée pour la charge."""

    MAINTAIN = "maintain"
    REDUCE_SLIGHTLY = "reduce_slightly"
    REDUCE = "reduce"
    REDUCE_STRONGLY = "reduce_strongly"
    SUSPEND = "suspend"


class ProgressionAdjustment(StrEnum):
    """Effet recommandé sur la progression planifiée."""

    CONTINUE = "continue"
    SLOW = "slow"
    PAUSE = "pause"
    REBUILD = "rebuild"


@dataclass(frozen=True, slots=True)
class TrajectoryAdjustment:
    """Décision du moteur concernant la trajectoire.

    Les champs décrivent les modifications du cadre d'entraînement.

    Ils ne prescrivent ni exercices, ni intervalles, ni séance
    détaillée.
    """

    reason: str

    severity: AdjustmentSeverity

    load: LoadAdjustment
    progression: ProgressionAdjustment

    restricted_modalities: tuple[
        TrainingModality,
        ...
    ] = ()

    protected_stimuli: tuple[
        TrainingStimulus,
        ...
    ] = ()

    suppressed_stimuli: tuple[
        TrainingStimulus,
        ...
    ] = ()

    allow_schedule_compression: bool = True

    requires_return_to_training: bool = False

    athlete_override_allowed: bool = True

    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.reason.strip():
            raise ValueError(
                "La raison de l'adaptation ne peut pas être vide."
            )

        overlap = (
            set(self.protected_stimuli)
            & set(self.suppressed_stimuli)
        )

        if overlap:
            raise ValueError(
                "Un stimulus ne peut pas être simultanément "
                "protégé et supprimé."
            )

        if (
            self.progression
            is ProgressionAdjustment.REBUILD
            and not self.requires_return_to_training
        ):
            raise ValueError(
                "Une reconstruction de progression doit déclencher "
                "un retour progressif à l'entraînement."
            )
