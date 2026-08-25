"""Progression des stimuli qualitatifs à l'intérieur d'une phase.

La prescription de phase définit les adaptations générales recherchées.
Ce module sélectionne ensuite la variante qualitative adaptée à la
position de la semaine dans la phase.

Il ne choisit ni le jour, ni la structure précise de séance.
"""

from __future__ import annotations

from dataclasses import replace

from opencoach.planning.stimulus.phase_prescription import (
    PhaseStimulusPrescription,
)
from opencoach.planning.stimulus.training import (
    TrainingStimulus,
)
from opencoach.planning.weekly.training_envelope import (
    TrainingPhase,
)


_BASE_QUALITY_SEQUENCE = (
    TrainingStimulus.SPEED_DEVELOPMENT,
    TrainingStimulus.SPEED_DEVELOPMENT,
    TrainingStimulus.VO2MAX,
)


def apply_phase_stimulus_progression(
    *,
    prescription: PhaseStimulusPrescription,
    phase_week_index: int,
) -> PhaseStimulusPrescription:
    """Applique la progression qualitative intra-phase."""

    if phase_week_index < 1:
        raise ValueError(
            "L'indice de semaine dans la phase "
            "doit être supérieur ou égal à 1."
        )

    if prescription.phase is not TrainingPhase.BASE:
        return prescription

    expected_stimulus = (
        _BASE_QUALITY_SEQUENCE[
            (phase_week_index - 1)
            % len(_BASE_QUALITY_SEQUENCE)
        ]
    )

    vo2_requirement = prescription.requirement_for(
        TrainingStimulus.VO2MAX
    )

    if vo2_requirement is None:
        raise ValueError(
            "La prescription BASE doit contenir "
            "un stimulus VO2MAX de référence."
        )

    requirements = tuple(
        (
            replace(
                requirement,
                stimulus=expected_stimulus,
            )
            if (
                requirement.stimulus
                is TrainingStimulus.VO2MAX
            )
            else requirement
        )
        for requirement in prescription.requirements
    )

    return PhaseStimulusPrescription(
        phase=prescription.phase,
        requirements=requirements,
    )
