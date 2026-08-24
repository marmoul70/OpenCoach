"""Modèles de prescription d'intensité OpenCoach.

Ces objets représentent des cibles d'entraînement concrètes sans
dépendre de leur affichage dans l'interface ou d'un fournisseur
extérieur.

La prescription peut combiner plusieurs références :

- perception de l'effort (RPE) ;
- fréquence cardiaque ;
- pourcentage de VMA.

Le RPE reste disponible comme référence robuste lorsque les données
physiologiques sont absentes ou insuffisamment fiables.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from opencoach.planning.stimulus.training import (
    TrainingStimulus,
)


class IntensityReference(StrEnum):
    """Référence utilisée pour exprimer une intensité."""

    RPE = "rpe"
    HEART_RATE = "heart_rate"
    HEART_RATE_RESERVE = "heart_rate_reserve"
    VMA_PERCENT = "vma_percent"


@dataclass(frozen=True, slots=True)
class IntensityRange:
    """Plage d'intensité exprimée avec une référence donnée."""

    reference: IntensityReference

    minimum: float
    maximum: float

    unit: str

    label: str

    def __post_init__(
        self,
    ) -> None:
        if self.minimum < 0:
            raise ValueError(
                "La borne minimale d'intensité "
                "ne peut pas être négative."
            )

        if self.maximum < self.minimum:
            raise ValueError(
                "La borne maximale d'intensité "
                "ne peut pas être inférieure "
                "à la borne minimale."
            )

        if not self.unit.strip():
            raise ValueError(
                "L'unité d'intensité ne peut pas être vide."
            )

        if not self.label.strip():
            raise ValueError(
                "Le libellé d'intensité ne peut pas être vide."
            )


@dataclass(frozen=True, slots=True)
class SessionIntensityPrescription:
    """Prescription d'intensité associée à un stimulus."""

    stimulus: TrainingStimulus

    primary_target: IntensityRange

    secondary_targets: tuple[
        IntensityRange,
        ...,
    ] = ()

    guidance: tuple[
        str,
        ...,
    ] = ()

    @property
    def targets(
        self,
    ) -> tuple[
        IntensityRange,
        ...,
    ]:
        """Retourne toutes les cibles dans leur ordre de priorité."""

        return (
            self.primary_target,
            *self.secondary_targets,
        )

    def target_for(
        self,
        reference: IntensityReference,
    ) -> IntensityRange | None:
        """Retourne la cible associée à une référence."""

        return next(
            (
                target
                for target in self.targets
                if target.reference is reference
            ),
            None,
        )
