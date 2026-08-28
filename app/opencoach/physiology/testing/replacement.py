"""Politique de remplacement d'un test physiologique refusé."""

from __future__ import annotations

from opencoach.physiology.testing.models import (
    PhysiologicalTestType,
)
from opencoach.physiology.testing.proposal import (
    PhysiologicalTestReplacementStimulus,
)


_TEST_REPLACEMENT_STIMULUS: dict[
    PhysiologicalTestType,
    PhysiologicalTestReplacementStimulus,
] = {
    PhysiologicalTestType.HALF_COOPER: (
        PhysiologicalTestReplacementStimulus.AEROBIC_POWER
    ),

    PhysiologicalTestType.COOPER_12_MIN: (
        PhysiologicalTestReplacementStimulus.AEROBIC_POWER
    ),

    PhysiologicalTestType.VAMEVAL: (
        PhysiologicalTestReplacementStimulus.AEROBIC_POWER
    ),

    PhysiologicalTestType.THRESHOLD_20_MIN: (
        PhysiologicalTestReplacementStimulus.THRESHOLD
    ),

    PhysiologicalTestType.THRESHOLD_30_MIN: (
        PhysiologicalTestReplacementStimulus.THRESHOLD
    ),

    PhysiologicalTestType.CRITICAL_SPEED_MULTI_EFFORT: (
        PhysiologicalTestReplacementStimulus.AEROBIC_POWER
    ),

    PhysiologicalTestType.UPHILL_6_MIN: (
        PhysiologicalTestReplacementStimulus.UPHILL_INTENSITY
    ),

    PhysiologicalTestType.UPHILL_20_MIN: (
        PhysiologicalTestReplacementStimulus.UPHILL_INTENSITY
    ),

    PhysiologicalTestType.INCREMENTRAIL: (
        PhysiologicalTestReplacementStimulus.UPHILL_INTENSITY
    ),

    PhysiologicalTestType.TRAIL_DURABILITY: (
        PhysiologicalTestReplacementStimulus.LONG_TRAIL_QUALITY
    ),
}


def get_test_replacement_stimulus(
    protocol: PhysiologicalTestType,
) -> PhysiologicalTestReplacementStimulus:
    """Retourne le stimulus à conserver si le test est refusé."""

    try:
        return _TEST_REPLACEMENT_STIMULUS[
            protocol
        ]

    except KeyError as exc:
        raise KeyError(
            "Aucun stimulus de remplacement "
            f"pour le protocole {protocol}."
        ) from exc
