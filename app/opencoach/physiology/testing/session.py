"""Séances concrètes utilisées pour les tests physiologiques.

Ce module transforme un protocole physiologique abstrait en séance
exécutable par l'athlète.

Il reste indépendant :
- du modèle persistant TrainingSession ;
- de l'API ;
- d'Intervals.icu.

Une couche d'adaptation reliera ces objets au planning OpenCoach
dans une mission ultérieure.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from opencoach.physiology.testing.models import (
    PhysiologicalTestType,
)


class PhysiologicalTestSegmentType(StrEnum):
    """Nature d'un segment d'une séance de test."""

    WARMUP = "warmup"
    PREPARATION = "preparation"
    TEST = "test"
    RECOVERY = "recovery"
    COOLDOWN = "cooldown"


class PhysiologicalTestSegmentIntensity(StrEnum):
    """Consigne d'intensité simplifiée."""

    EASY = "easy"
    MODERATE = "moderate"
    HARD = "hard"
    MAXIMAL = "maximal"


@dataclass(
    frozen=True,
    slots=True,
)
class PhysiologicalTestSessionSegment:
    """Une partie structurée de la séance."""

    segment_type: PhysiologicalTestSegmentType

    title: str
    instruction: str

    intensity: PhysiologicalTestSegmentIntensity

    duration_seconds: int | None = None

    repetitions: int | None = None
    repetition_duration_seconds: int | None = None
    recovery_duration_seconds: int | None = None

    analysis_window: bool = False

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError(
                "Le titre du segment est obligatoire."
            )

        if not self.instruction.strip():
            raise ValueError(
                "L'instruction du segment est obligatoire."
            )

        for value in (
            self.duration_seconds,
            self.repetitions,
            self.repetition_duration_seconds,
            self.recovery_duration_seconds,
        ):
            if (
                value is not None
                and value <= 0
            ):
                raise ValueError(
                    "Les durées et répétitions doivent "
                    "être strictement positives."
                )

        if (
            self.analysis_window
            and self.segment_type
            is not PhysiologicalTestSegmentType.TEST
        ):
            raise ValueError(
                "Seul un segment de test peut être "
                "utilisé comme fenêtre d'analyse."
            )


@dataclass(
    frozen=True,
    slots=True,
)
class PhysiologicalTestSession:
    """Séance complète générée pour un protocole."""

    protocol: PhysiologicalTestType

    title: str
    description: str

    segments: tuple[
        PhysiologicalTestSessionSegment,
        ...,
    ]

    terrain_requirements: tuple[
        str,
        ...,
    ]

    execution_notes: tuple[
        str,
        ...,
    ]

    expected_total_duration_minutes: int

    metadata: tuple[
        tuple[str, str],
        ...,
    ]

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError(
                "Le titre de la séance est obligatoire."
            )

        if not self.description.strip():
            raise ValueError(
                "La description de la séance est obligatoire."
            )

        if not self.segments:
            raise ValueError(
                "Une séance de test doit contenir "
                "au moins un segment."
            )

        if (
            self.expected_total_duration_minutes
            <= 0
        ):
            raise ValueError(
                "La durée totale estimée doit être positive."
            )

        analysis_segments = tuple(
            segment
            for segment in self.segments
            if segment.analysis_window
        )

        if len(analysis_segments) != 1:
            raise ValueError(
                "Une séance de test doit posséder "
                "exactement une fenêtre d'analyse."
            )

    @property
    def analysis_segment(
        self,
    ) -> PhysiologicalTestSessionSegment:
        """Retourne le segment à analyser automatiquement."""

        return next(
            segment
            for segment in self.segments
            if segment.analysis_window
        )

    def metadata_dict(
        self,
    ) -> dict[str, str]:
        """Retourne les métadonnées sous forme de dictionnaire."""

        return dict(
            self.metadata
        )
