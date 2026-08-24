"""Prescription physiologique déterministe des séances OpenCoach."""

from __future__ import annotations

from dataclasses import dataclass

from opencoach.planning.physiology.snapshot import (
    PhysiologicalCalibrationMetric,
    PhysiologicalCalibrationSnapshot,
)
from opencoach.planning.sessions.prescription.models import (
    IntensityRange,
    IntensityReference,
    SessionIntensityPrescription,
)
from opencoach.planning.stimulus.training import (
    TrainingStimulus,
)


@dataclass(frozen=True, slots=True)
class StimulusIntensityPolicy:
    """Politique générique d'intensité d'un stimulus."""

    rpe_min: float
    rpe_max: float

    hrr_min: float | None = None
    hrr_max: float | None = None

    hrmax_min: float | None = None
    hrmax_max: float | None = None

    vma_min: float | None = None
    vma_max: float | None = None

    prefer_threshold_hr2: bool = False

    guidance: tuple[
        str,
        ...,
    ] = ()

    def __post_init__(
        self,
    ) -> None:
        if not (
            0 <= self.rpe_min
            <= self.rpe_max
            <= 10
        ):
            raise ValueError(
                "La plage RPE doit être comprise entre 0 et 10."
            )


INTENSITY_POLICIES: dict[
    TrainingStimulus,
    StimulusIntensityPolicy,
] = {
    TrainingStimulus.RECOVERY: (
        StimulusIntensityPolicy(
            rpe_min=1,
            rpe_max=2,
            hrr_min=0.50,
            hrr_max=0.60,
            hrmax_min=0.60,
            hrmax_max=0.68,
            guidance=(
                "La séance doit rester très facile.",
                "Terminer avec davantage de fraîcheur qu'au départ.",
            ),
        )
    ),

    TrainingStimulus.AEROBIC_EASY: (
        StimulusIntensityPolicy(
            rpe_min=2,
            rpe_max=3,
            hrr_min=0.55,
            hrr_max=0.70,
            hrmax_min=0.65,
            hrmax_max=0.75,
            vma_min=60,
            vma_max=70,
            guidance=(
                "Maintenir une respiration confortable.",
                "La conversation doit rester facile.",
            ),
        )
    ),

    TrainingStimulus.AEROBIC_ENDURANCE: (
        StimulusIntensityPolicy(
            rpe_min=3,
            rpe_max=4,
            hrr_min=0.60,
            hrr_max=0.75,
            hrmax_min=0.68,
            hrmax_max=0.80,
            vma_min=65,
            vma_max=75,
            guidance=(
                "Maintenir un effort aérobie régulier et maîtrisé.",
            ),
        )
    ),

    TrainingStimulus.LONG_ENDURANCE: (
        StimulusIntensityPolicy(
            rpe_min=3,
            rpe_max=4,
            hrr_min=0.55,
            hrr_max=0.72,
            hrmax_min=0.65,
            hrmax_max=0.78,
            vma_min=60,
            vma_max=72,
            guidance=(
                "Privilégier la régularité plutôt que la vitesse.",
                "Adapter l'allure au relief sur terrain trail.",
            ),
        )
    ),

    TrainingStimulus.THRESHOLD: (
        StimulusIntensityPolicy(
            rpe_min=7,
            rpe_max=8,
            vma_min=80,
            vma_max=90,
            prefer_threshold_hr2=True,
            guidance=(
                "L'effort doit être soutenu mais contrôlé.",
                "Éviter de transformer la séance en effort maximal.",
            ),
        )
    ),

    TrainingStimulus.UPHILL_THRESHOLD: (
        StimulusIntensityPolicy(
            rpe_min=7,
            rpe_max=8,
            prefer_threshold_hr2=True,
            guidance=(
                "Maintenir un effort régulier dans la montée.",
                "La fréquence cardiaque est prioritaire sur l'allure.",
            ),
        )
    ),

    TrainingStimulus.VO2MAX: (
        StimulusIntensityPolicy(
            rpe_min=8,
            rpe_max=9,
            vma_min=95,
            vma_max=105,
            guidance=(
                "L'intensité concerne les fractions de travail.",
                "La fréquence cardiaque n'est pas utilisée comme "
                "cible principale sur les fractions courtes.",
            ),
        )
    ),

    TrainingStimulus.UPHILL_STRENGTH: (
        StimulusIntensityPolicy(
            rpe_min=7,
            rpe_max=8,
            guidance=(
                "La qualité gestuelle et la force priment sur "
                "la fréquence cardiaque.",
            ),
        )
    ),

    TrainingStimulus.UPHILL_STRENGTH_ENDURANCE: (
        StimulusIntensityPolicy(
            rpe_min=7,
            rpe_max=8,
            guidance=(
                "Réaliser la chaise avec une tension musculaire "
                "contrôlée sans aller à l'échec.",
                "Enchaîner la côte avec une course puissante "
                "et techniquement propre.",
                "Utiliser la descente comme récupération active.",
                "La fréquence cardiaque n'est pas une cible "
                "pertinente pour ce circuit.",
            ),
        )
    ),

    TrainingStimulus.DOWNHILL_SPECIFICITY: (
        StimulusIntensityPolicy(
            rpe_min=4,
            rpe_max=6,
            guidance=(
                "L'intensité cardiovasculaire n'est pas l'objectif "
                "principal.",
                "Prioriser les appuis, la cadence et le contrôle.",
            ),
        )
    ),

    TrainingStimulus.RACE_SPECIFIC: (
        StimulusIntensityPolicy(
            rpe_min=5,
            rpe_max=8,
            guidance=(
                "L'intensité dépend des contraintes de la course "
                "objectif.",
            ),
        )
    ),

    TrainingStimulus.STRENGTH_LOWER_BODY: (
        StimulusIntensityPolicy(
            rpe_min=6,
            rpe_max=8,
            guidance=(
                "Conserver une exécution technique propre.",
                "Éviter l'échec musculaire systématique.",
            ),
        )
    ),

    TrainingStimulus.STRENGTH_CORE: (
        StimulusIntensityPolicy(
            rpe_min=5,
            rpe_max=7,
            guidance=(
                "Privilégier le contrôle et la stabilité.",
            ),
        )
    ),
}


def build_intensity_prescription(
    *,
    stimulus: TrainingStimulus,
    physiology: PhysiologicalCalibrationSnapshot | None,
) -> SessionIntensityPrescription:
    """Construit une prescription adaptée aux données disponibles."""

    policy = INTENSITY_POLICIES[
        stimulus
    ]

    rpe = _build_rpe_target(
        policy
    )

    physiological_targets = (
        _build_physiological_targets(
            policy=policy,
            physiology=physiology,
        )
    )

    if physiological_targets:
        primary = physiological_targets[
            0
        ]

        secondary = (
            *physiological_targets[1:],
            rpe,
        )

    else:
        primary = rpe
        secondary = ()

    return SessionIntensityPrescription(
        stimulus=stimulus,
        primary_target=primary,
        secondary_targets=secondary,
        guidance=policy.guidance,
    )


def validate_intensity_policy_catalog() -> None:
    """Vérifie que tous les stimuli disposent d'une politique."""

    missing = tuple(
        stimulus
        for stimulus in TrainingStimulus
        if stimulus not in INTENSITY_POLICIES
    )

    if missing:
        values = ", ".join(
            stimulus.value
            for stimulus in missing
        )

        raise RuntimeError(
            "Le catalogue de prescription est incomplet : "
            f"{values}."
        )


def _build_rpe_target(
    policy: StimulusIntensityPolicy,
) -> IntensityRange:
    return IntensityRange(
        reference=IntensityReference.RPE,
        minimum=policy.rpe_min,
        maximum=policy.rpe_max,
        unit="/10",
        label="Perception de l'effort",
    )


def _build_physiological_targets(
    *,
    policy: StimulusIntensityPolicy,
    physiology: PhysiologicalCalibrationSnapshot | None,
) -> tuple[
    IntensityRange,
    ...,
]:
    if physiology is None:
        return ()

    targets: list[
        IntensityRange
    ] = []

    if policy.prefer_threshold_hr2:
        threshold_target = (
            _build_threshold_hr2_target(
                physiology.threshold_heart_rate_2
            )
        )

        if threshold_target is not None:
            targets.append(
                threshold_target
            )

    heart_rate_target = (
        _build_heart_rate_target(
            policy=policy,
            physiology=physiology,
        )
    )

    if heart_rate_target is not None:
        targets.append(
            heart_rate_target
        )

    vma_target = (
        _build_vma_target(
            policy=policy,
            physiology=physiology,
        )
    )

    if vma_target is not None:
        targets.append(
            vma_target
        )

    return _deduplicate_references(
        targets
    )


def _build_threshold_hr2_target(
    metric: PhysiologicalCalibrationMetric,
) -> IntensityRange | None:
    if not _usable_value(
        metric
    ):
        return None

    assert metric.value is not None

    threshold = metric.value

    return IntensityRange(
        reference=IntensityReference.HEART_RATE,
        minimum=round(
            threshold * 0.95
        ),
        maximum=round(
            threshold
        ),
        unit="bpm",
        label="FC proche du second seuil",
    )


def _build_heart_rate_target(
    *,
    policy: StimulusIntensityPolicy,
    physiology: PhysiologicalCalibrationSnapshot,
) -> IntensityRange | None:
    max_hr = physiology.max_heart_rate
    resting_hr = physiology.resting_heart_rate

    if (
        policy.hrr_min is not None
        and policy.hrr_max is not None
        and _usable_value(max_hr)
        and _usable_value(resting_hr)
    ):
        assert max_hr.value is not None
        assert resting_hr.value is not None

        reserve = (
            max_hr.value
            - resting_hr.value
        )

        minimum = (
            resting_hr.value
            + reserve * policy.hrr_min
        )

        maximum = (
            resting_hr.value
            + reserve * policy.hrr_max
        )

        return IntensityRange(
            reference=(
                IntensityReference
                .HEART_RATE_RESERVE
            ),
            minimum=round(
                minimum
            ),
            maximum=round(
                maximum
            ),
            unit="bpm",
            label="Fréquence cardiaque individualisée",
        )

    if (
        policy.hrmax_min is not None
        and policy.hrmax_max is not None
        and _usable_value(max_hr)
    ):
        assert max_hr.value is not None

        return IntensityRange(
            reference=IntensityReference.HEART_RATE,
            minimum=round(
                max_hr.value
                * policy.hrmax_min
            ),
            maximum=round(
                max_hr.value
                * policy.hrmax_max
            ),
            unit="bpm",
            label="Fréquence cardiaque",
        )

    return None


def _build_vma_target(
    *,
    policy: StimulusIntensityPolicy,
    physiology: PhysiologicalCalibrationSnapshot,
) -> IntensityRange | None:
    if (
        policy.vma_min is None
        or policy.vma_max is None
        or not _usable_value(
            physiology.vma
        )
    ):
        return None

    return IntensityRange(
        reference=IntensityReference.VMA_PERCENT,
        minimum=policy.vma_min,
        maximum=policy.vma_max,
        unit="% VMA",
        label="Pourcentage de VMA",
    )


def _usable_value(
    metric: PhysiologicalCalibrationMetric,
) -> bool:
    return (
        metric.usable
        and metric.value is not None
        and metric.value > 0
    )


def _deduplicate_references(
    targets: list[
        IntensityRange
    ],
) -> tuple[
    IntensityRange,
    ...,
]:
    result: list[
        IntensityRange
    ] = []

    references: set[
        IntensityReference
    ] = set()

    for target in targets:
        if target.reference in references:
            continue

        result.append(
            target
        )

        references.add(
            target.reference
        )

    return tuple(
        result
    )
