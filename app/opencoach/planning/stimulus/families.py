"""Familles physiologiques des stimuli OpenCoach.

Une famille regroupe des stimuli poursuivant une adaptation
physiologique comparable.

Appartenir à une même famille ne signifie pas nécessairement que
les stimuli sont mutuellement exclusifs. Les règles de
contextualisation décident ensuite si une variante plus spécifique
remplace une variante générique.
"""

from __future__ import annotations

from enum import StrEnum

from opencoach.planning.stimulus.training import (
    TrainingStimulus,
)


class StimulusFamily(StrEnum):
    """Grande famille physiologique ou fonctionnelle."""

    AEROBIC = "aerobic"
    THRESHOLD = "threshold"
    HIGH_INTENSITY = "high_intensity"
    STRENGTH = "strength"
    SPECIFIC = "specific"
    RECOVERY = "recovery"


_STIMULUS_FAMILIES: dict[
    TrainingStimulus,
    StimulusFamily,
] = {
    TrainingStimulus.AEROBIC_EASY:
        StimulusFamily.AEROBIC,
    TrainingStimulus.AEROBIC_ENDURANCE:
        StimulusFamily.AEROBIC,
    TrainingStimulus.LONG_ENDURANCE:
        StimulusFamily.AEROBIC,

    TrainingStimulus.THRESHOLD:
        StimulusFamily.THRESHOLD,
    TrainingStimulus.UPHILL_THRESHOLD:
        StimulusFamily.THRESHOLD,

    TrainingStimulus.VO2MAX:
        StimulusFamily.HIGH_INTENSITY,

    TrainingStimulus.STRENGTH_LOWER_BODY:
        StimulusFamily.STRENGTH,
    TrainingStimulus.STRENGTH_CORE:
        StimulusFamily.STRENGTH,
    TrainingStimulus.UPHILL_STRENGTH:
        StimulusFamily.STRENGTH,
    TrainingStimulus.UPHILL_STRENGTH_ENDURANCE:
        StimulusFamily.STRENGTH,

    TrainingStimulus.DOWNHILL_SPECIFICITY:
        StimulusFamily.SPECIFIC,
    TrainingStimulus.RACE_SPECIFIC:
        StimulusFamily.SPECIFIC,

    TrainingStimulus.RECOVERY:
        StimulusFamily.RECOVERY,
}


def stimulus_family(
    stimulus: TrainingStimulus,
) -> StimulusFamily:
    """Retourne la famille associée à un stimulus."""

    try:
        return _STIMULUS_FAMILIES[
            stimulus
        ]
    except KeyError as exc:
        raise ValueError(
            "Aucune famille définie pour le stimulus "
            f"'{stimulus.value}'."
        ) from exc


def same_stimulus_family(
    first: TrainingStimulus,
    second: TrainingStimulus,
) -> bool:
    """Indique si deux stimuli appartiennent à la même famille."""

    return (
        stimulus_family(first)
        is stimulus_family(second)
    )
