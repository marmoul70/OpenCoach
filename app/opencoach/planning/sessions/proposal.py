"""Proposition concrète de séance générée par le coach IA.

Une SessionProposal décrit le contenu concret proposé pour une
SessionIntent déjà décidée par le moteur déterministe.

Le moteur Python reste responsable des contraintes structurelles :
- jour ;
- durée disponible ;
- modalité ;
- stimuli ;
- importance ;
- charge et trajectoire.

Le coach IA peut proposer la manière concrète de réaliser la séance,
mais ne peut pas redéfinir ces contraintes.
"""

from __future__ import annotations

from dataclasses import dataclass

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

    def __post_init__(self) -> None:
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
    """Séance concrète proposée par le coach IA."""

    title: str

    modality: TrainingModality

    duration_minutes: int

    covered_stimuli: tuple[
        TrainingStimulus,
        ...
    ]

    blocks: tuple[
        SessionBlock,
        ...
    ]

    objective: str

    coach_notes: tuple[
        str,
        ...
    ] = ()

    def __post_init__(self) -> None:
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

        if len(
            set(self.covered_stimuli)
        ) != len(
            self.covered_stimuli
        ):
            raise ValueError(
                "Les stimuli couverts ne peuvent pas être dupliqués."
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
            and block_duration != self.duration_minutes
        ):
            raise ValueError(
                "La somme des durées des blocs doit correspondre "
                "à la durée totale de la séance."
            )
