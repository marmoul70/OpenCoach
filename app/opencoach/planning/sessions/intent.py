"""Intentions de séance produites à partir des stimuli hebdomadaires.

Une SessionIntent décrit ce qu'une séance doit accomplir sans définir
son contenu concret.

Elle constitue la frontière entre :
- le moteur déterministe Python, qui décide des objectifs et contraintes ;
- le moteur de génération des séances, qui produit ensuite la séance concrète.

Une intention peut regrouper plusieurs stimuli compatibles. Cela évite
de transformer artificiellement chaque stimulus en séance distincte.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from opencoach.planning.stimulus.training import (
    SpecificityLevel,
    StimulusPriority,
    SubstitutionPolicy,
    TrainingModality,
    TrainingStimulus,
    TrainingStimulusRequirement,
)


class SessionIntentImportance(StrEnum):
    """Importance structurelle d'une intention de séance."""

    SUPPORT = "support"
    IMPORTANT = "important"
    KEY = "key"


@dataclass(frozen=True, slots=True)
class SessionIntent:
    """Intention abstraite d'une séance.

    primary_stimulus
        Objectif principal de la séance.

    secondary_stimuli
        Objectifs complémentaires pouvant être obtenus au cours de
        la même séance.

    preferred_modalities
        Modalités privilégiées lorsque plusieurs choix restent
        compatibles avec l'intention.

    required_modalities
        Modalités imposées par au moins un stimulus non substituable.

    Le modèle ne contient volontairement ni exercices, ni intervalles,
    ni allures concrètes.
    """

    primary_stimulus: TrainingStimulus

    secondary_stimuli: tuple[
        TrainingStimulus,
        ...
    ]

    importance: SessionIntentImportance

    specificity: SpecificityLevel

    substitution: SubstitutionPolicy

    preferred_modalities: tuple[
        TrainingModality,
        ...
    ]

    required_modalities: tuple[
        TrainingModality,
        ...
    ]

    duration_min_minutes: int | None = None
    duration_max_minutes: int | None = None

    required: bool = True

    source_requirements: tuple[
        TrainingStimulusRequirement,
        ...
    ] = ()

    def __post_init__(self) -> None:
        if (
            self.primary_stimulus
            in self.secondary_stimuli
        ):
            raise ValueError(
                "Le stimulus principal ne peut pas également "
                "être secondaire."
            )

        if (
            len(self.secondary_stimuli)
            != len(set(self.secondary_stimuli))
        ):
            raise ValueError(
                "Un stimulus secondaire ne peut apparaître "
                "qu'une seule fois."
            )

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
            and self.duration_min_minutes
            > self.duration_max_minutes
        ):
            raise ValueError(
                "La durée minimale ne peut pas dépasser "
                "la durée maximale."
            )

        if (
            self.substitution
            is SubstitutionPolicy.FORBIDDEN
            and not self.required_modalities
        ):
            raise ValueError(
                "Une intention non substituable doit définir "
                "au moins une modalité obligatoire."
            )

    @property
    def stimuli(
        self,
    ) -> tuple[
        TrainingStimulus,
        ...
    ]:
        """Retourne tous les stimuli couverts par l'intention."""

        return (
            self.primary_stimulus,
            *self.secondary_stimuli,
        )

    def covers(
        self,
        stimulus: TrainingStimulus,
    ) -> bool:
        """Indique si l'intention couvre un stimulus."""

        return stimulus in self.stimuli


def build_session_intent(
    *,
    primary: TrainingStimulusRequirement,
    secondary: tuple[
        TrainingStimulusRequirement,
        ...
    ] = (),
) -> SessionIntent:
    """Construit une intention depuis des requirements compatibles.

    Cette fonction consolide uniquement leurs contraintes.

    La décision de savoir quels requirements doivent être regroupés
    appartient à une couche ultérieure.
    """

    requirements = (
        primary,
        *secondary,
    )

    _validate_distinct_requirements(
        requirements
    )

    required_modalities = (
        _resolve_required_modalities(
            requirements
        )
    )

    preferred_modalities = (
        _resolve_preferred_modalities(
            requirements=requirements,
            required_modalities=required_modalities,
        )
    )

    return SessionIntent(
        primary_stimulus=primary.stimulus,
        secondary_stimuli=tuple(
            requirement.stimulus
            for requirement in secondary
        ),
        importance=_resolve_importance(
            requirements
        ),
        specificity=_resolve_specificity(
            requirements
        ),
        substitution=_resolve_substitution(
            requirements
        ),
        preferred_modalities=(
            preferred_modalities
        ),
        required_modalities=(
            required_modalities
        ),
        duration_min_minutes=(
            _resolve_duration_min(
                requirements
            )
        ),
        duration_max_minutes=(
            _resolve_duration_max(
                requirements
            )
        ),
        source_requirements=requirements,
    )


def _validate_distinct_requirements(
    requirements: tuple[
        TrainingStimulusRequirement,
        ...
    ],
) -> None:
    stimuli = tuple(
        requirement.stimulus
        for requirement in requirements
    )

    if len(stimuli) != len(set(stimuli)):
        raise ValueError(
            "Un même stimulus ne peut apparaître plusieurs fois "
            "dans une intention de séance."
        )


def _resolve_importance(
    requirements: tuple[
        TrainingStimulusRequirement,
        ...
    ],
) -> SessionIntentImportance:
    priorities = {
        requirement.priority
        for requirement in requirements
    }

    if StimulusPriority.KEY in priorities:
        return SessionIntentImportance.KEY

    if StimulusPriority.IMPORTANT in priorities:
        return SessionIntentImportance.IMPORTANT

    return SessionIntentImportance.SUPPORT


def _resolve_specificity(
    requirements: tuple[
        TrainingStimulusRequirement,
        ...
    ],
) -> SpecificityLevel:
    order = {
        SpecificityLevel.LOW: 0,
        SpecificityLevel.MODERATE: 1,
        SpecificityLevel.HIGH: 2,
        SpecificityLevel.VERY_HIGH: 3,
    }

    return max(
        (
            requirement.specificity
            for requirement in requirements
        ),
        key=order.__getitem__,
    )


def _resolve_substitution(
    requirements: tuple[
        TrainingStimulusRequirement,
        ...
    ],
) -> SubstitutionPolicy:
    order = {
        SubstitutionPolicy.ALLOWED: 0,
        SubstitutionPolicy.CONDITIONAL: 1,
        SubstitutionPolicy.FORBIDDEN: 2,
    }

    return max(
        (
            requirement.substitution
            for requirement in requirements
        ),
        key=order.__getitem__,
    )


def _resolve_required_modalities(
    requirements: tuple[
        TrainingStimulusRequirement,
        ...
    ],
) -> tuple[
    TrainingModality,
    ...
]:
    constrained_sets = [
        set(requirement.required_modalities)
        for requirement in requirements
        if requirement.required_modalities
    ]

    if not constrained_sets:
        return ()

    compatible = set.intersection(
        *constrained_sets
    )

    if not compatible:
        raise ValueError(
            "Les stimuli regroupés imposent des modalités "
            "incompatibles."
        )

    return _ordered_modalities(
        compatible
    )


def _resolve_preferred_modalities(
    *,
    requirements: tuple[
        TrainingStimulusRequirement,
        ...
    ],
    required_modalities: tuple[
        TrainingModality,
        ...
    ],
) -> tuple[
    TrainingModality,
    ...
]:
    preferred: list[
        TrainingModality
    ] = []

    for requirement in requirements:
        for modality in (
            requirement.preferred_modalities
        ):
            if modality not in preferred:
                preferred.append(
                    modality
                )

    if required_modalities:
        preferred = [
            modality
            for modality in preferred
            if modality in required_modalities
        ]

        if not preferred:
            return required_modalities

    return tuple(
        preferred
    )


def _resolve_duration_min(
    requirements: tuple[
        TrainingStimulusRequirement,
        ...
    ],
) -> int | None:
    values = [
        requirement.duration_min_minutes
        for requirement in requirements
        if (
            requirement.duration_min_minutes
            is not None
        )
    ]

    if not values:
        return None

    return max(
        values
    )


def _resolve_duration_max(
    requirements: tuple[
        TrainingStimulusRequirement,
        ...
    ],
) -> int | None:
    values = [
        requirement.duration_max_minutes
        for requirement in requirements
        if (
            requirement.duration_max_minutes
            is not None
        )
    ]

    if not values:
        return None

    result = min(
        values
    )

    minimum = _resolve_duration_min(
        requirements
    )

    if (
        minimum is not None
        and minimum > result
    ):
        raise ValueError(
            "Les contraintes de durée des stimuli regroupés "
            "sont incompatibles."
        )

    return result


def _ordered_modalities(
    modalities: set[
        TrainingModality
    ],
) -> tuple[
    TrainingModality,
    ...
]:
    return tuple(
        modality
        for modality in TrainingModality
        if modality in modalities
    )
