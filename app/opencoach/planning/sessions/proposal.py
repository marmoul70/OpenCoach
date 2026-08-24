"""Proposition concrète de séance produite par OpenCoach.

Une SessionProposal décrit le contenu concret associé à une
SessionIntent déjà décidée par le moteur déterministe.

Le moteur Python reste responsable des contraintes structurelles :
- jour ;
- durée disponible ;
- modalité ;
- stimuli ;
- importance ;
- charge et trajectoire.

La proposition matérialise ces contraintes sous forme :
- de blocs temporels ;
- d'une prescription d'intensité ;
- d'une structure de travail concrète.
"""

from __future__ import annotations

from dataclasses import dataclass

from opencoach.planning.sessions.prescription.intervals import (
    WorkStructure,
)
from opencoach.planning.sessions.prescription.models import (
    SessionIntensityPrescription,
)
from opencoach.planning.stimulus.training import (
    TrainingModality,
    TrainingStimulus,
)


@dataclass(frozen=True, slots=True)
class SessionBlock:
    """Bloc constitutif d'une séance proposée."""

    name: str

    description: str

    duration_minutes: int | None = None

    def __post_init__(
        self,
    ) -> None:
        if not self.name.strip():
            raise ValueError(
                "Le nom du bloc ne peut pas être vide."
            )

        if not self.description.strip():
            raise ValueError(
                "La description du bloc ne peut pas être vide."
            )

        if (
            self.duration_minutes is not None
            and self.duration_minutes <= 0
        ):
            raise ValueError(
                "La durée d'un bloc doit être "
                "strictement positive."
            )


@dataclass(frozen=True, slots=True)
class SessionProposal:
    """Séance concrète générée par OpenCoach."""

    title: str

    modality: TrainingModality

    duration_minutes: int

    covered_stimuli: tuple[
        TrainingStimulus,
        ...,
    ]

    blocks: tuple[
        SessionBlock,
        ...,
    ]

    objective: str

    intensity_prescription: (
        SessionIntensityPrescription
        | None
    ) = None

    work_structure: (
        WorkStructure
        | None
    ) = None

    coach_notes: tuple[
        str,
        ...,
    ] = ()

    def __post_init__(
        self,
    ) -> None:
        if not self.title.strip():
            raise ValueError(
                "Le titre de la séance ne peut pas être vide."
            )

        if self.duration_minutes <= 0:
            raise ValueError(
                "La durée de la séance doit être "
                "strictement positive."
            )

        if not self.covered_stimuli:
            raise ValueError(
                "Une séance doit couvrir au moins un stimulus."
            )

        if not self.blocks:
            raise ValueError(
                "Une séance doit contenir au moins un bloc."
            )

        if not self.objective.strip():
            raise ValueError(
                "L'objectif de la séance ne peut pas être vide."
            )

        if (
            len(
                set(
                    self.covered_stimuli
                )
            )
            != len(
                self.covered_stimuli
            )
        ):
            raise ValueError(
                "Les stimuli couverts ne peuvent pas être dupliqués."
            )

        if (
            self.intensity_prescription is not None
            and (
                self.intensity_prescription.stimulus
                not in self.covered_stimuli
            )
        ):
            raise ValueError(
                "La prescription d'intensité doit concerner "
                "un stimulus couvert par la séance."
            )

        if (
            self.work_structure is not None
            and (
                self.work_structure.stimulus
                not in self.covered_stimuli
            )
        ):
            raise ValueError(
                "La structure de travail doit concerner "
                "un stimulus couvert par la séance."
            )

        block_duration = sum(
            block.duration_minutes
            for block in self.blocks
            if block.duration_minutes is not None
        )

        fully_timed = all(
            block.duration_minutes is not None
            for block in self.blocks
        )

        if (
            fully_timed
            and block_duration
            != self.duration_minutes
        ):
            raise ValueError(
                "La somme des durées des blocs doit correspondre "
                "à la durée totale de la séance."
            )
