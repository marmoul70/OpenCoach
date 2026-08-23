"""Prescription déterministe des stimuli selon la phase d'entraînement.

Ce module décrit les qualités que la semaine doit développer.

Il ne choisit ni les jours, ni les exercices, ni les intervalles,
ni le contenu concret des séances. Ces décisions appartiennent aux
étapes ultérieures du moteur et au moteur de génération des séances.
"""

from __future__ import annotations

from dataclasses import dataclass

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
class PhaseStimulusPrescription:
    """Stimuli attendus pour une phase donnée."""

    phase: TrainingPhase

    requirements: tuple[
        TrainingStimulusRequirement,
        ...
    ]

    def __post_init__(self) -> None:
        stimuli = tuple(
            requirement.stimulus
            for requirement in self.requirements
        )

        if len(stimuli) != len(set(stimuli)):
            raise ValueError(
                "Un stimulus ne peut apparaître qu'une seule fois "
                "dans une prescription de phase."
            )

    def requirement_for(
        self,
        stimulus: TrainingStimulus,
    ) -> TrainingStimulusRequirement | None:
        """Retourne la prescription associée à un stimulus."""

        for requirement in self.requirements:
            if requirement.stimulus is stimulus:
                return requirement

        return None


def _easy_aerobic_requirement() -> TrainingStimulusRequirement:
    return TrainingStimulusRequirement(
        stimulus=TrainingStimulus.AEROBIC_EASY,
        priority=StimulusPriority.SUPPORT,
        specificity=SpecificityLevel.LOW,
        substitution=SubstitutionPolicy.ALLOWED,
        preferred_modalities=(
            TrainingModality.RUNNING,
            TrainingModality.CYCLING,
            TrainingModality.SWIMMING,
        ),
        duration_min_minutes=30,
        duration_max_minutes=120,
    )


def _long_endurance_requirement(
    *,
    specificity: SpecificityLevel,
) -> TrainingStimulusRequirement:
    return TrainingStimulusRequirement(
        stimulus=TrainingStimulus.LONG_ENDURANCE,
        priority=StimulusPriority.KEY,
        specificity=specificity,
        substitution=SubstitutionPolicy.CONDITIONAL,
        preferred_modalities=(
            TrainingModality.TRAIL_RUNNING,
            TrainingModality.RUNNING,
        ),
        duration_min_minutes=60,
        duration_max_minutes=300,
    )


def _strength_lower_body_requirement() -> TrainingStimulusRequirement:
    return TrainingStimulusRequirement(
        stimulus=TrainingStimulus.STRENGTH_LOWER_BODY,
        priority=StimulusPriority.SUPPORT,
        specificity=SpecificityLevel.MODERATE,
        substitution=SubstitutionPolicy.CONDITIONAL,
        preferred_modalities=(
            TrainingModality.STRENGTH,
        ),
        duration_min_minutes=15,
        duration_max_minutes=60,
    )


def _strength_core_requirement() -> TrainingStimulusRequirement:
    return TrainingStimulusRequirement(
        stimulus=TrainingStimulus.STRENGTH_CORE,
        priority=StimulusPriority.SUPPORT,
        specificity=SpecificityLevel.MODERATE,
        substitution=SubstitutionPolicy.CONDITIONAL,
        preferred_modalities=(
            TrainingModality.STRENGTH,
        ),
        duration_min_minutes=10,
        duration_max_minutes=45,
    )


def _threshold_requirement() -> TrainingStimulusRequirement:
    return TrainingStimulusRequirement(
        stimulus=TrainingStimulus.THRESHOLD,
        priority=StimulusPriority.KEY,
        specificity=SpecificityLevel.MODERATE,
        substitution=SubstitutionPolicy.FORBIDDEN,
        required_modalities=(
            TrainingModality.RUNNING,
            TrainingModality.TRAIL_RUNNING,
        ),
        preferred_modalities=(
            TrainingModality.RUNNING,
            TrainingModality.TRAIL_RUNNING,
        ),
        duration_min_minutes=30,
        duration_max_minutes=120,
    )


def build_phase_stimulus_prescription(
    phase: TrainingPhase,
) -> PhaseStimulusPrescription:
    """Construit la prescription de stimuli d'une phase."""

    if phase is TrainingPhase.FOUNDATION:
        requirements = (
            _easy_aerobic_requirement(),
            _strength_lower_body_requirement(),
            _strength_core_requirement(),
        )

    elif phase is TrainingPhase.BASE:
        requirements = (
            _easy_aerobic_requirement(),
            _long_endurance_requirement(
                specificity=SpecificityLevel.LOW,
            ),
            _strength_lower_body_requirement(),
            _strength_core_requirement(),
        )

    elif phase is TrainingPhase.BUILD:
        requirements = (
            _easy_aerobic_requirement(),
            _threshold_requirement(),
            _long_endurance_requirement(
                specificity=SpecificityLevel.MODERATE,
            ),
            _strength_lower_body_requirement(),
            _strength_core_requirement(),
        )

    elif phase is TrainingPhase.SPECIFIC:
        requirements = (
            _easy_aerobic_requirement(),
            _threshold_requirement(),
            _long_endurance_requirement(
                specificity=SpecificityLevel.HIGH,
            ),
            _strength_lower_body_requirement(),
            _strength_core_requirement(),
        )

    elif phase is TrainingPhase.TAPER:
        requirements = (
            _easy_aerobic_requirement(),
            _threshold_requirement(),
        )

    elif phase is TrainingPhase.RECOVERY:
        requirements = (
            _easy_aerobic_requirement(),
        )

    elif phase is TrainingPhase.RETURN_TO_TRAINING:
        requirements = (
            _easy_aerobic_requirement(),
            _strength_lower_body_requirement(),
            _strength_core_requirement(),
        )

    else:
        raise ValueError(
            f"Phase d'entraînement non prise en charge : {phase}"
        )

    return PhaseStimulusPrescription(
        phase=phase,
        requirements=requirements,
    )
