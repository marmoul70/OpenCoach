"""Quantification hebdomadaire des besoins en stimuli.

Ce module transforme une prescription qualitative de stimuli en
demande hebdomadaire quantifiée.

Il répond à la question :

    combien d'expositions à chaque stimulus sont souhaitées
    cette semaine ?

Il ne choisit :
- ni les jours ;
- ni les séances ;
- ni les exercices ;
- ni les intervalles ;
- ni la combinaison de plusieurs stimuli dans une même séance.

Ces responsabilités appartiennent aux étapes ultérieures du moteur
et au moteur de génération des séances.

Les quantités définies ici sont des règles de planification OpenCoach.
Elles sont configurables et ne constituent pas des seuils médicaux.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from opencoach.planning.stimulus.contextual_prescription import (
    ContextualStimulusPrescription,
)
from opencoach.planning.trajectory.multi_week import (
    TrajectoryWeekType,
)
from opencoach.planning.stimulus.training import (
    StimulusPriority,
    TrainingStimulus,
    TrainingStimulusRequirement,
)
from opencoach.planning.weekly.training_envelope import (
    TrainingPhase,
)


class StimulusDemandDensity(StrEnum):
    """Densité qualitative globale autorisée pour la semaine."""

    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


@dataclass(frozen=True, slots=True)
class StimulusDemand:
    """Demande hebdomadaire associée à un stimulus.

    minimum_occurrences
        Nombre minimal d'expositions que les étapes suivantes
        doivent essayer de préserver.

    target_occurrences
        Nombre d'expositions souhaité dans des conditions normales.

    maximum_occurrences
        Limite structurelle empêchant les étapes suivantes de
        multiplier arbitrairement un stimulus.

    Une occurrence représente une exposition au stimulus, pas
    nécessairement une séance distincte. Plusieurs stimuli pourront
    ultérieurement partager une même intention de séance.
    """

    requirement: TrainingStimulusRequirement

    minimum_occurrences: int
    target_occurrences: int
    maximum_occurrences: int

    def __post_init__(self) -> None:
        values = (
            self.minimum_occurrences,
            self.target_occurrences,
            self.maximum_occurrences,
        )

        if any(value < 0 for value in values):
            raise ValueError(
                "Les nombres d'occurrences ne peuvent pas être négatifs."
            )

        if (
            self.minimum_occurrences
            > self.target_occurrences
        ):
            raise ValueError(
                "Le minimum d'occurrences ne peut pas dépasser "
                "la cible."
            )

        if (
            self.target_occurrences
            > self.maximum_occurrences
        ):
            raise ValueError(
                "La cible d'occurrences ne peut pas dépasser "
                "le maximum."
            )

    @property
    def stimulus(self) -> TrainingStimulus:
        """Retourne le stimulus concerné."""

        return self.requirement.stimulus

    @property
    def required(self) -> bool:
        """Indique si au moins une exposition est obligatoire."""

        return self.minimum_occurrences > 0

    @property
    def suppressed(self) -> bool:
        """Indique si le stimulus est totalement neutralisé."""

        return self.maximum_occurrences == 0


@dataclass(frozen=True, slots=True)
class WeeklyStimulusDemand:
    """Demande qualitative complète d'une semaine."""

    phase: TrainingPhase

    week_type: TrajectoryWeekType

    target_load: float
    reference_load: float

    load_ratio: float | None

    density: StimulusDemandDensity

    demands: tuple[
        StimulusDemand,
        ...
    ]

    maximum_key_exposures: int

    def __post_init__(self) -> None:
        if self.target_load < 0:
            raise ValueError(
                "La charge cible ne peut pas être négative."
            )

        if self.reference_load < 0:
            raise ValueError(
                "La charge de référence ne peut pas être négative."
            )

        if self.maximum_key_exposures < 0:
            raise ValueError(
                "Le nombre maximal d'expositions clés "
                "ne peut pas être négatif."
            )

        stimuli = tuple(
            demand.stimulus
            for demand in self.demands
        )

        if len(stimuli) != len(set(stimuli)):
            raise ValueError(
                "Un stimulus ne peut apparaître qu'une seule fois "
                "dans la demande hebdomadaire."
            )

    def demand_for(
        self,
        stimulus: TrainingStimulus,
    ) -> StimulusDemand | None:
        """Retourne la demande associée à un stimulus."""

        for demand in self.demands:
            if demand.stimulus is stimulus:
                return demand

        return None

    @property
    def minimum_exposure_count(self) -> int:
        """Nombre minimal total d'expositions demandées."""

        return sum(
            demand.minimum_occurrences
            for demand in self.demands
        )

    @property
    def target_exposure_count(self) -> int:
        """Nombre total d'expositions souhaitées.

        Ce nombre n'est pas un nombre de séances : plusieurs
        expositions pourront être combinées dans une même séance.
        """

        return sum(
            demand.target_occurrences
            for demand in self.demands
        )


def build_weekly_stimulus_demand(
    *,
    prescription: ContextualStimulusPrescription,
    week_type: TrajectoryWeekType,
    target_load: float,
    reference_load: float,
    phase_week_index: int = 1,
) -> WeeklyStimulusDemand:
    """Quantifie la prescription pour une semaine donnée."""

    if phase_week_index < 1:
        raise ValueError(
            "L'index de semaine dans la phase doit être positif."
        )

    if target_load < 0:
        raise ValueError(
            "La charge cible ne peut pas être négative."
        )

    if reference_load < 0:
        raise ValueError(
            "La charge de référence ne peut pas être négative."
        )

    load_ratio = (
        target_load / reference_load
        if reference_load > 0
        else None
    )

    if (
        target_load == 0
        or week_type
        is TrajectoryWeekType.SUSPENDED
    ):
        demands = tuple(
            _suppressed_demand(
                requirement
            )
            for requirement
            in prescription.requirements
        )

        return WeeklyStimulusDemand(
            phase=prescription.phase,
            week_type=week_type,
            target_load=target_load,
            reference_load=reference_load,
            load_ratio=load_ratio,
            density=StimulusDemandDensity.NONE,
            demands=demands,
            maximum_key_exposures=0,
        )

    if (
        week_type
        is TrajectoryWeekType.RECOVERY
    ):
        demands = tuple(
            _recovery_demand(
                requirement
            )
            for requirement
            in prescription.requirements
        )

        return WeeklyStimulusDemand(
            phase=prescription.phase,
            week_type=week_type,
            target_load=target_load,
            reference_load=reference_load,
            load_ratio=load_ratio,
            density=StimulusDemandDensity.LOW,
            demands=demands,
            maximum_key_exposures=1,
        )

    if (
        week_type
        is TrajectoryWeekType.TAPER
    ):
        demands = tuple(
            _taper_demand(
                requirement
            )
            for requirement
            in prescription.requirements
        )

        return WeeklyStimulusDemand(
            phase=prescription.phase,
            week_type=week_type,
            target_load=target_load,
            reference_load=reference_load,
            load_ratio=load_ratio,
            density=StimulusDemandDensity.LOW,
            demands=demands,
            maximum_key_exposures=1,
        )

    if (
        week_type
        is TrajectoryWeekType.RETURN_TO_TRAINING
    ):
        demands = tuple(
            _return_to_training_demand(
                requirement
            )
            for requirement
            in prescription.requirements
        )

        return WeeklyStimulusDemand(
            phase=prescription.phase,
            week_type=week_type,
            target_load=target_load,
            reference_load=reference_load,
            load_ratio=load_ratio,
            density=StimulusDemandDensity.LOW,
            demands=demands,
            maximum_key_exposures=0,
        )

    demands = tuple(
        _loading_demand(
            requirement=requirement,
            load_ratio=load_ratio,
            phase=prescription.phase,
            phase_week_index=phase_week_index,
        )
        for requirement
        in prescription.requirements
    )

    return WeeklyStimulusDemand(
        phase=prescription.phase,
        week_type=week_type,
        target_load=target_load,
        reference_load=reference_load,
        load_ratio=load_ratio,
        density=_loading_density(
            load_ratio=load_ratio,
        ),
        demands=demands,
        maximum_key_exposures=2,
    )


def _requires_loading_week(
    stimulus: TrainingStimulus,
) -> bool:
    """Indique si un stimulus est réservé aux semaines de charge.

    Ces stimuli produisent une fatigue spécifique suffisamment
    importante pour être exclus des semaines de récupération,
    d'affûtage et de reprise.
    """

    return (
        stimulus
        is TrainingStimulus.UPHILL_STRENGTH_ENDURANCE
    )


def _loading_demand(
    *,
    requirement: TrainingStimulusRequirement,
    load_ratio: float | None,
    phase: TrainingPhase,
    phase_week_index: int,
) -> StimulusDemand:
    """Quantifie un stimulus pendant une semaine de développement."""

    if (
        requirement.stimulus
        is TrainingStimulus.UPHILL_STRENGTH_ENDURANCE
        and phase is TrainingPhase.BUILD
        and phase_week_index == 1
    ):
        return _suppressed_demand(
            requirement
        )

    if (
        requirement.stimulus
        is TrainingStimulus.AEROBIC_EASY
    ):
        target_occurrences = (
            2
            if (
                load_ratio is None
                or load_ratio >= 1.0
            )
            else 1
        )

        return StimulusDemand(
            requirement=requirement,
            minimum_occurrences=0,
            target_occurrences=target_occurrences,
            maximum_occurrences=3,
        )

    if (
        requirement.priority
        is StimulusPriority.KEY
    ):
        return StimulusDemand(
            requirement=requirement,
            minimum_occurrences=1,
            target_occurrences=1,
            maximum_occurrences=1,
        )

    if (
        requirement.priority
        is StimulusPriority.IMPORTANT
    ):
        return StimulusDemand(
            requirement=requirement,
            minimum_occurrences=0,
            target_occurrences=1,
            maximum_occurrences=1,
        )

    return StimulusDemand(
        requirement=requirement,
        minimum_occurrences=0,
        target_occurrences=1,
        maximum_occurrences=2,
    )


def _recovery_demand(
    requirement: TrainingStimulusRequirement,
) -> StimulusDemand:
    """Réduit la densité qualitative d'une semaine de récupération.

    Les stimuli clés restent disponibles pour les étapes suivantes,
    mais ne sont plus obligatoires individuellement.

    maximum_key_exposures=1 au niveau de la semaine empêchera
    ultérieurement la multiplication des sollicitations clés.
    """

    if _requires_loading_week(
        requirement.stimulus
    ):
        return _suppressed_demand(
            requirement
        )

    if (
        requirement.stimulus
        is TrainingStimulus.AEROBIC_EASY
    ):
        return StimulusDemand(
            requirement=requirement,
            minimum_occurrences=1,
            target_occurrences=2,
            maximum_occurrences=3,
        )

    if (
        requirement.priority
        is StimulusPriority.KEY
    ):
        return StimulusDemand(
            requirement=requirement,
            minimum_occurrences=0,
            target_occurrences=0,
            maximum_occurrences=1,
        )

    if (
        requirement.priority
        is StimulusPriority.IMPORTANT
    ):
        return StimulusDemand(
            requirement=requirement,
            minimum_occurrences=0,
            target_occurrences=0,
            maximum_occurrences=1,
        )

    return StimulusDemand(
        requirement=requirement,
        minimum_occurrences=0,
        target_occurrences=1,
        maximum_occurrences=1,
    )


def _taper_demand(
    requirement: TrainingStimulusRequirement,
) -> StimulusDemand:
    """Préserve peu de qualité pendant l'affûtage."""

    if _requires_loading_week(
        requirement.stimulus
    ):
        return _suppressed_demand(
            requirement
        )

    if (
        requirement.priority
        is StimulusPriority.KEY
    ):
        return StimulusDemand(
            requirement=requirement,
            minimum_occurrences=1,
            target_occurrences=1,
            maximum_occurrences=1,
        )

    if (
        requirement.stimulus
        is TrainingStimulus.AEROBIC_EASY
    ):
        return StimulusDemand(
            requirement=requirement,
            minimum_occurrences=0,
            target_occurrences=1,
            maximum_occurrences=2,
        )

    return StimulusDemand(
        requirement=requirement,
        minimum_occurrences=0,
        target_occurrences=0,
        maximum_occurrences=1,
    )


def _return_to_training_demand(
    requirement: TrainingStimulusRequirement,
) -> StimulusDemand:
    """Produit une demande conservatrice pendant une reprise."""

    if _requires_loading_week(
        requirement.stimulus
    ):
        return _suppressed_demand(
            requirement
        )

    if (
        requirement.stimulus
        is TrainingStimulus.AEROBIC_EASY
    ):
        return StimulusDemand(
            requirement=requirement,
            minimum_occurrences=1,
            target_occurrences=2,
            maximum_occurrences=3,
        )

    if (
        requirement.priority
        is StimulusPriority.KEY
    ):
        return StimulusDemand(
            requirement=requirement,
            minimum_occurrences=0,
            target_occurrences=0,
            maximum_occurrences=0,
        )

    return StimulusDemand(
        requirement=requirement,
        minimum_occurrences=0,
        target_occurrences=1,
        maximum_occurrences=1,
    )


def _suppressed_demand(
    requirement: TrainingStimulusRequirement,
) -> StimulusDemand:
    """Neutralise complètement un stimulus."""

    return StimulusDemand(
        requirement=requirement,
        minimum_occurrences=0,
        target_occurrences=0,
        maximum_occurrences=0,
    )


def _loading_density(
    *,
    load_ratio: float | None,
) -> StimulusDemandDensity:
    """Classe la densité structurelle d'une semaine de charge.

    Le ratio est utilisé uniquement comme information relative à la
    trajectoire. Il ne représente aucun seuil physiologique médical.
    """

    if load_ratio is None:
        return StimulusDemandDensity.MODERATE

    if load_ratio < 1.0:
        return StimulusDemandDensity.MODERATE

    return StimulusDemandDensity.HIGH
