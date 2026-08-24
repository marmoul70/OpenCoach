"""Contextualisation des stimuli selon la phase et la course cible.

Ce module combine :
- la logique générale de la phase ;
- le profil objectif de la compétition.

Il ne génère aucune séance concrète.
"""

from __future__ import annotations

from dataclasses import dataclass

from opencoach.planning.stimulus.phase_prescription import (
    PhaseStimulusPrescription,
    build_phase_stimulus_prescription,
)
from opencoach.planning.stimulus.families import (
    same_stimulus_family,
)
from opencoach.planning.knowledge.race_demand_profile import (
    RaceDemandProfile,
    RaceSpecificityDemand,
)
from opencoach.planning.stimulus.training import (
    SpecificityLevel,
    StimulusPriority,
    SubstitutionPolicy,
    TrainingModality,
    TrainingStimulus,
    TrainingStimulusRequirement,
)
from opencoach.planning.weekly.training_envelope import (
    TrainingPhase,
)


@dataclass(frozen=True, slots=True)
class ContextualStimulusPrescription:
    """Prescription de stimuli adaptée à la course cible."""

    phase: TrainingPhase
    race_profile: RaceDemandProfile

    requirements: tuple[
        TrainingStimulusRequirement,
        ...
    ]

    def requirement_for(
        self,
        stimulus: TrainingStimulus,
    ) -> TrainingStimulusRequirement | None:
        for requirement in self.requirements:
            if requirement.stimulus is stimulus:
                return requirement

        return None


def build_contextual_stimulus_prescription(
    *,
    phase: TrainingPhase,
    race_profile: RaceDemandProfile,
) -> ContextualStimulusPrescription:
    """Combine phase générale et demandes spécifiques de la course."""

    base = build_phase_stimulus_prescription(
        phase
    )

    requirements = list(
        base.requirements
    )

    if phase in {
        TrainingPhase.BUILD,
        TrainingPhase.SPECIFIC,
    }:
        _append_race_specific_requirements(
            requirements=requirements,
            race_profile=race_profile,
            phase=phase,
        )

    requirements = _apply_contextual_specializations(
        requirements
    )

    requirements = _deduplicate_requirements(
        requirements
    )

    return ContextualStimulusPrescription(
        phase=phase,
        race_profile=race_profile,
        requirements=tuple(
            requirements
        ),
    )


def _append_race_specific_requirements(
    *,
    requirements: list[
        TrainingStimulusRequirement
    ],
    race_profile: RaceDemandProfile,
    phase: TrainingPhase,
) -> None:
    if race_profile.uphill_demand in {
        RaceSpecificityDemand.HIGH,
        RaceSpecificityDemand.VERY_HIGH,
    }:
        requirements.append(
            _uphill_strength_requirement(
                phase=phase
            )
        )

        requirements.append(
            _uphill_strength_endurance_requirement(
                phase=phase
            )
        )

    if (
        race_profile.uphill_demand
        is RaceSpecificityDemand.VERY_HIGH
    ):
        requirements.append(
            _uphill_threshold_requirement(
                phase=phase
            )
        )

    if race_profile.downhill_demand in {
        RaceSpecificityDemand.HIGH,
        RaceSpecificityDemand.VERY_HIGH,
    }:
        requirements.append(
            _downhill_specificity_requirement(
                phase=phase
            )
        )

    if race_profile.race_specific_demand in {
        RaceSpecificityDemand.HIGH,
        RaceSpecificityDemand.VERY_HIGH,
    }:
        requirements.append(
            _race_specific_requirement(
                phase=phase
            )
        )


def _uphill_strength_requirement(
    *,
    phase: TrainingPhase,
) -> TrainingStimulusRequirement:
    return TrainingStimulusRequirement(
        stimulus=TrainingStimulus.UPHILL_STRENGTH,
        priority=(
            StimulusPriority.KEY
            if phase is TrainingPhase.SPECIFIC
            else StimulusPriority.IMPORTANT
        ),
        specificity=(
            SpecificityLevel.VERY_HIGH
            if phase is TrainingPhase.SPECIFIC
            else SpecificityLevel.HIGH
        ),
        substitution=SubstitutionPolicy.FORBIDDEN,
        required_modalities=(
            TrainingModality.TRAIL_RUNNING,
        ),
        duration_min_minutes=20,
        duration_max_minutes=120,
    )


def _uphill_strength_endurance_requirement(
    *,
    phase: TrainingPhase,
) -> TrainingStimulusRequirement:
    """Force-endurance spécifique en côte sous pré-fatigue musculaire."""

    return TrainingStimulusRequirement(
        stimulus=(
            TrainingStimulus.UPHILL_STRENGTH_ENDURANCE
        ),
        priority=StimulusPriority.IMPORTANT,
        specificity=(
            SpecificityLevel.VERY_HIGH
            if phase is TrainingPhase.SPECIFIC
            else SpecificityLevel.HIGH
        ),
        substitution=SubstitutionPolicy.FORBIDDEN,
        required_modalities=(
            TrainingModality.TRAIL_RUNNING,
        ),
        duration_min_minutes=45,
        duration_max_minutes=75,
    )


def _uphill_threshold_requirement(
    *,
    phase: TrainingPhase,
) -> TrainingStimulusRequirement:
    return TrainingStimulusRequirement(
        stimulus=TrainingStimulus.UPHILL_THRESHOLD,
        priority=StimulusPriority.KEY,
        specificity=(
            SpecificityLevel.VERY_HIGH
            if phase is TrainingPhase.SPECIFIC
            else SpecificityLevel.HIGH
        ),
        substitution=SubstitutionPolicy.FORBIDDEN,
        required_modalities=(
            TrainingModality.TRAIL_RUNNING,
        ),
        duration_min_minutes=30,
        duration_max_minutes=120,
    )


def _downhill_specificity_requirement(
    *,
    phase: TrainingPhase,
) -> TrainingStimulusRequirement:
    return TrainingStimulusRequirement(
        stimulus=TrainingStimulus.DOWNHILL_SPECIFICITY,
        priority=(
            StimulusPriority.KEY
            if phase is TrainingPhase.SPECIFIC
            else StimulusPriority.IMPORTANT
        ),
        specificity=(
            SpecificityLevel.VERY_HIGH
            if phase is TrainingPhase.SPECIFIC
            else SpecificityLevel.HIGH
        ),
        substitution=SubstitutionPolicy.FORBIDDEN,
        required_modalities=(
            TrainingModality.TRAIL_RUNNING,
        ),
        duration_min_minutes=20,
        duration_max_minutes=120,
    )


def _race_specific_requirement(
    *,
    phase: TrainingPhase,
) -> TrainingStimulusRequirement:
    return TrainingStimulusRequirement(
        stimulus=TrainingStimulus.RACE_SPECIFIC,
        priority=StimulusPriority.KEY,
        specificity=(
            SpecificityLevel.VERY_HIGH
            if phase is TrainingPhase.SPECIFIC
            else SpecificityLevel.HIGH
        ),
        substitution=SubstitutionPolicy.FORBIDDEN,
        required_modalities=(
            TrainingModality.TRAIL_RUNNING,
            TrainingModality.RUNNING,
        ),
        duration_min_minutes=45,
        duration_max_minutes=300,
    )


_SPECIALIZED_STIMULUS_REPLACEMENTS: dict[
    TrainingStimulus,
    TrainingStimulus,
] = {
    TrainingStimulus.THRESHOLD:
        TrainingStimulus.UPHILL_THRESHOLD,
}


def _apply_contextual_specializations(
    requirements: list[
        TrainingStimulusRequirement
    ],
) -> list[
    TrainingStimulusRequirement
]:
    """Remplace une variante générique par sa variante spécialisée.

    Une substitution n'est appliquée que si les deux stimuli sont
    réellement présents dans la prescription contextualisée et
    appartiennent à la même famille physiologique.
    """

    present = {
        requirement.stimulus
        for requirement in requirements
    }

    suppressed: set[
        TrainingStimulus
    ] = set()

    for (
        generic,
        specialized,
    ) in _SPECIALIZED_STIMULUS_REPLACEMENTS.items():
        if (
            generic not in present
            or specialized not in present
        ):
            continue

        if not same_stimulus_family(
            generic,
            specialized,
        ):
            raise ValueError(
                "Une spécialisation de stimulus doit rester "
                "dans la même famille physiologique."
            )

        suppressed.add(
            generic
        )

    return [
        requirement
        for requirement in requirements
        if requirement.stimulus
        not in suppressed
    ]


def _deduplicate_requirements(
    requirements: list[
        TrainingStimulusRequirement
    ],
) -> list[
    TrainingStimulusRequirement
]:
    """Conserve une seule prescription par stimulus.

    La dernière occurrence gagne, ce qui permet au profil de course
    de renforcer une prescription générale.
    """

    deduplicated: dict[
        TrainingStimulus,
        TrainingStimulusRequirement,
    ] = {}

    for requirement in requirements:
        deduplicated[
            requirement.stimulus
        ] = requirement

    return list(
        deduplicated.values()
    )
