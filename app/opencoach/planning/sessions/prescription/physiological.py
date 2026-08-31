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

    heart_rate_zone: str | None = None

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
            heart_rate_zone="z1",
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

    TrainingStimulus.PRE_RACE_ACTIVATION: (
        StimulusIntensityPolicy(
            rpe_min=2,
            rpe_max=4,
            hrr_min=0.50,
            hrr_max=0.68,
            hrmax_min=0.60,
            hrmax_max=0.74,
            guidance=(
                "Conserver une charge globale très faible.",
                "Les accélérations doivent rester courtes, "
                "fluides et techniquement propres.",
                "Terminer la séance avec une sensation de fraîcheur.",
                "Aucune fatigue résiduelle ne doit être recherchée.",
            ),
        )
    ),

    TrainingStimulus.AEROBIC_EASY: (
        StimulusIntensityPolicy(
            rpe_min=2,
            rpe_max=3,
            heart_rate_zone="z2",
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
            heart_rate_zone="z2",
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
            heart_rate_zone="z2",
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
            heart_rate_zone="z4",
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
            heart_rate_zone="z4",
            prefer_threshold_hr2=True,
            guidance=(
                "Maintenir un effort régulier dans la montée.",
                "La fréquence cardiaque est prioritaire sur l'allure.",
            ),
        )
    ),

    TrainingStimulus.SPEED_DEVELOPMENT: (
        StimulusIntensityPolicy(
            rpe_min=7,
            rpe_max=9,
            vma_min=100,
            vma_max=115,
            guidance=(
                "La priorité est la qualité de course "
                "et non l'épuisement.",
                "Conserver une vitesse élevée avec une "
                "technique propre sur chaque répétition.",
                "La fréquence cardiaque n'est pas une cible "
                "pertinente sur les fractions très courtes.",
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


def canonical_intensity_for_stimulus(
    stimulus: TrainingStimulus,
) -> str:
    """Retourne le niveau d'intensité canonique d'un stimulus."""

    policy = INTENSITY_POLICIES[
        stimulus
    ]

    rpe_max = policy.rpe_max

    if rpe_max <= 2:
        return "very_easy"

    if rpe_max <= 4:
        return "easy"

    if rpe_max <= 6:
        return "moderate"

    if rpe_max <= 8:
        return "hard"

    return "very_hard"


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
    personalized = (
        _build_personalized_heart_rate_zone_target(
            policy=policy,
            physiology=physiology,
        )
    )

    if personalized is not None:
        return personalized

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
            label="FC",
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
            label="FC",
        )

    return None


def _build_personalized_heart_rate_zone_target(
    *,
    policy: StimulusIntensityPolicy,
    physiology: PhysiologicalCalibrationSnapshot,
) -> IntensityRange | None:
    zone_name = policy.heart_rate_zone

    if zone_name is None:
        return None

    zones = physiology.heart_rate_zones

    names = (
        "z1",
        "z2",
        "z3",
        "z4",
        "z5",
    )

    if zone_name not in names:
        return None

    zone = getattr(
        zones,
        zone_name,
    )

    if zone is None:
        return None

    index = names.index(
        zone_name
    )

    if index == 0:
        minimum = (
            physiology.resting_heart_rate.value
            if _usable_value(
                physiology.resting_heart_rate
            )
            else 1
        )
    else:
        previous = getattr(
            zones,
            names[index - 1],
        )

        if previous is None:
            return None

        minimum = previous.max_bpm + 1

    return IntensityRange(
        reference=IntensityReference.HEART_RATE,
        minimum=round(
            minimum
        ),
        maximum=zone.max_bpm,
        unit="bpm",
        label=zone_name.upper(),
    )


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

    assert physiology.vma.value is not None

    vma_kmh = physiology.vma.value

    speed_min_kmh = (
        vma_kmh
        * policy.vma_min
        / 100
    )

    speed_max_kmh = (
        vma_kmh
        * policy.vma_max
        / 100
    )

    pace_fastest_seconds_per_km = (
        3600
        / speed_max_kmh
    )

    pace_slowest_seconds_per_km = (
        3600
        / speed_min_kmh
    )

    return IntensityRange(
        reference=IntensityReference.VMA_PERCENT,
        minimum=policy.vma_min,
        maximum=policy.vma_max,
        unit="% VMA",
        label="Pourcentage de VMA",
        speed_min_kmh=round(
            speed_min_kmh,
            2,
        ),
        speed_max_kmh=round(
            speed_max_kmh,
            2,
        ),
        pace_fastest_seconds_per_km=round(
            pace_fastest_seconds_per_km,
            1,
        ),
        pace_slowest_seconds_per_km=round(
            pace_slowest_seconds_per_km,
            1,
        ),
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
