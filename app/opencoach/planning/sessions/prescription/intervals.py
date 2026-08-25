"""Prescription déterministe des structures de travail OpenCoach.

Ce module transforme une durée utile et un stimulus en structure
d'entraînement concrète.

Les durées de répétition peuvent être exprimées en secondes afin de
représenter correctement les fractions courtes, notamment pour :

- VO2max ;
- force en côte ;
- travail technique court.

Les calculs internes utilisent les secondes afin d'éviter toute
approximation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from opencoach.planning.sessions.prescription.distance_target import (
    DistanceRepetitionTarget,
)

from opencoach.planning.stimulus.training import (
    TrainingStimulus,
)
from opencoach.planning.weekly.training_envelope import (
    TrainingPhase,
)


class WorkStructureType(StrEnum):
    """Famille de structure utilisée pour un bloc principal."""

    CONTINUOUS = "continuous"
    INTERVALS = "intervals"
    REPEATS = "repeats"
    TECHNICAL = "technical"
    STRENGTH = "strength"
    CIRCUIT = "circuit"


class CircuitStepType(StrEnum):
    """Nature d'une étape dans un circuit composite."""

    STRENGTH = "strength"
    WORK = "work"
    RECOVERY = "recovery"


@dataclass(frozen=True, slots=True)
class CircuitStep:
    """Étape élémentaire d'un circuit composite."""

    step_type: CircuitStepType
    duration_seconds: int
    description: str

    def __post_init__(self) -> None:
        if self.duration_seconds <= 0:
            raise ValueError(
                "La durée d'une étape de circuit doit être positive."
            )

        if not self.description.strip():
            raise ValueError(
                "La description d'une étape de circuit ne peut pas être vide."
            )


@dataclass(frozen=True, slots=True)
class WorkCircuit:
    """Circuit composite répété plusieurs fois."""

    repetitions: int
    steps: tuple[
        CircuitStep,
        ...
    ]

    def __post_init__(self) -> None:
        if self.repetitions <= 0:
            raise ValueError(
                "Le nombre de répétitions d'un circuit doit être positif."
            )

        if not self.steps:
            raise ValueError(
                "Un circuit doit contenir au moins une étape."
            )

    @property
    def cycle_duration_seconds(self) -> int:
        return sum(
            step.duration_seconds
            for step in self.steps
        )

    @property
    def total_duration_seconds(self) -> int:
        return (
            self.repetitions
            * self.cycle_duration_seconds
        )

    @property
    def total_duration_minutes(self) -> float:
        return (
            self.total_duration_seconds
            / 60
        )


class WorkDurationUnit(StrEnum):
    """Unité d'une durée de répétition."""

    SECONDS = "seconds"
    MINUTES = "minutes"


@dataclass(frozen=True, slots=True)
class WorkInterval:
    """Description d'une série de répétitions.

    Le travail peut être défini soit par une durée, soit par une
    distance. Ces deux représentations sont mutuellement exclusives.

    La récupération reste pour l'instant exprimée en durée.
    """

    repetitions: int

    work_duration: int | None = None
    work_unit: WorkDurationUnit | None = None

    work_distance_meters: int | None = None

    repetition_target: (
        DistanceRepetitionTarget
        | None
    ) = None

    recovery_duration: int | None = None
    recovery_unit: WorkDurationUnit | None = None

    def __post_init__(
        self,
    ) -> None:
        if self.repetitions <= 0:
            raise ValueError(
                "Le nombre de répétitions doit être positif."
            )

        has_duration = (
            self.work_duration is not None
            or self.work_unit is not None
        )

        has_distance = (
            self.work_distance_meters is not None
        )

        if has_duration and has_distance:
            raise ValueError(
                "Une répétition doit définir une durée ou une distance, "
                "mais pas les deux."
            )

        if not has_duration and not has_distance:
            raise ValueError(
                "Une répétition doit définir une durée ou une distance."
            )

        if (
            self.work_duration is None
            and self.work_unit is not None
        ):
            raise ValueError(
                "Une unité de travail ne peut pas être définie "
                "sans durée de travail."
            )

        if (
            self.work_duration is not None
            and self.work_unit is None
        ):
            raise ValueError(
                "Une unité de travail est obligatoire "
                "lorsqu'une durée de travail est définie."
            )

        if (
            self.work_duration is not None
            and self.work_duration <= 0
        ):
            raise ValueError(
                "La durée de travail doit être positive."
            )

        if (
            self.repetition_target is not None
            and self.work_distance_meters is None
        ):
            raise ValueError(
                "Une cible de répétition nécessite "
                "une distance de travail."
            )

        if (
            self.repetition_target is not None
            and (
                self.repetition_target.distance_meters
                != self.work_distance_meters
            )
        ):
            raise ValueError(
                "La cible de répétition doit correspondre "
                "à la distance de travail."
            )

        if (
            self.work_distance_meters is not None
            and self.work_distance_meters <= 0
        ):
            raise ValueError(
                "La distance de travail doit être positive."
            )

        if (
            self.recovery_duration is None
            and self.recovery_unit is not None
        ):
            raise ValueError(
                "Une unité de récupération ne peut pas être définie "
                "sans durée de récupération."
            )

        if (
            self.recovery_duration is not None
            and self.recovery_duration <= 0
        ):
            raise ValueError(
                "La durée de récupération doit être positive."
            )

        if (
            self.recovery_duration is not None
            and self.recovery_unit is None
        ):
            raise ValueError(
                "Une unité de récupération est obligatoire "
                "lorsqu'une durée de récupération est définie."
            )

    @property
    def work_seconds(
        self,
    ) -> int:
        """Durée d'une répétition de travail en secondes.

        Une répétition définie par distance ne possède pas encore
        de durée déterminée tant qu'aucune vitesse cible n'est connue.
        """

        if (
            self.work_duration is None
            or self.work_unit is None
        ):
            raise ValueError(
                "La durée de travail n'est pas disponible "
                "pour un intervalle défini par distance."
            )

        return _duration_to_seconds(
            value=self.work_duration,
            unit=self.work_unit,
        )

    @property
    def total_work_distance_meters(
        self,
    ) -> int:
        """Distance totale de travail lorsque la série est métrique."""

        if self.work_distance_meters is None:
            return 0

        return (
            self.repetitions
            * self.work_distance_meters
        )

    @property
    def recovery_seconds(
        self,
    ) -> int:
        """Durée d'une récupération en secondes."""

        if self.recovery_duration is None:
            return 0

        assert self.recovery_unit is not None

        return _duration_to_seconds(
            value=self.recovery_duration,
            unit=self.recovery_unit,
        )

    @property
    def total_work_seconds(
        self,
    ) -> int:
        """Temps cumulé de travail."""

        return (
            self.repetitions
            * self.work_seconds
        )

    @property
    def total_recovery_seconds(
        self,
    ) -> int:
        """Temps cumulé de récupération entre les répétitions."""

        if self.repetitions <= 1:
            return 0

        return (
            (self.repetitions - 1)
            * self.recovery_seconds
        )

    @property
    def total_duration_seconds(
        self,
    ) -> int:
        """Durée totale de la série."""

        return (
            self.total_work_seconds
            + self.total_recovery_seconds
        )

    @property
    def total_work_minutes(
        self,
    ) -> float:
        """Temps cumulé de travail en minutes."""

        return (
            self.total_work_seconds
            / 60
        )

    @property
    def total_duration_minutes(
        self,
    ) -> float:
        """Durée totale en minutes."""

        return (
            self.total_duration_seconds
            / 60
        )


@dataclass(frozen=True, slots=True)
class WorkStructure:
    """Structure concrète proposée pour le bloc principal."""

    structure_type: WorkStructureType

    stimulus: TrainingStimulus

    available_minutes: int

    intervals: tuple[
        WorkInterval,
        ...,
    ] = ()

    continuous_minutes: int | None = None

    circuit: WorkCircuit | None = None

    description: str = ""

    def __post_init__(
        self,
    ) -> None:
        if self.available_minutes <= 0:
            raise ValueError(
                "La durée disponible doit être positive."
            )

        if (
            self.continuous_minutes is not None
            and self.continuous_minutes <= 0
        ):
            raise ValueError(
                "La durée continue doit être positive."
            )

        if (
            self.continuous_minutes is not None
            and self.intervals
        ):
            raise ValueError(
                "Une structure ne peut pas être simultanément "
                "continue et fractionnée."
            )

        if (
            self.circuit is not None
            and self.intervals
        ):
            raise ValueError(
                "Une structure de circuit ne peut pas contenir "
                "des intervalles classiques."
            )

        if (
            self.circuit is not None
            and self.continuous_minutes is not None
        ):
            raise ValueError(
                "Une structure de circuit ne peut pas être "
                "simultanément continue."
            )


        if not self.description.strip():
            raise ValueError(
                "La description de la structure ne peut pas être vide."
            )

        if (
            self.planned_seconds
            > self.available_minutes * 60
        ):
            raise ValueError(
                "La structure de travail dépasse le temps disponible."
            )

    @property
    def planned_seconds(
        self,
    ) -> int:
        """Temps occupé par la structure en secondes."""

        if self.continuous_minutes is not None:
            return (
                self.continuous_minutes
                * 60
            )

        if self.circuit is not None:
            return (
                self.circuit.total_duration_seconds
            )

        total = 0

        for interval in self.intervals:
            if interval.work_distance_meters is not None:
                total += (
                    interval.repetitions
                    * _estimate_speed_repetition_seconds(
                        interval.work_distance_meters
                    )
                )

                total += (
                    max(
                        interval.repetitions - 1,
                        0,
                    )
                    * interval.recovery_seconds
                )

                continue

            total += interval.total_duration_seconds

        return total

    @property
    def planned_minutes(
        self,
    ) -> float:
        """Temps occupé par la structure en minutes."""

        return (
            self.planned_seconds
            / 60
        )


def build_work_structure(
    *,
    stimulus: TrainingStimulus,
    phase: TrainingPhase,
    available_minutes: int,
    phase_week_index: int = 1,
) -> WorkStructure:
    """Construit une structure compatible avec le stimulus."""

    if available_minutes <= 0:
        raise ValueError(
            "La durée disponible doit être positive."
        )

    if phase_week_index < 1:
        raise ValueError(
            "L'indice de semaine dans la phase "
            "doit être supérieur ou égal à 1."
        )

    if stimulus is TrainingStimulus.THRESHOLD:
        return _build_threshold(
            phase=phase,
            available_minutes=available_minutes,
            phase_week_index=phase_week_index,
        )

    if stimulus is TrainingStimulus.VO2MAX:
        return _build_vo2max(
            phase=phase,
            available_minutes=available_minutes,
            phase_week_index=phase_week_index,
        )

    if stimulus is TrainingStimulus.SPEED_DEVELOPMENT:
        return _build_speed_development(
            available_minutes=available_minutes,
            phase_week_index=phase_week_index,
        )

    if stimulus is TrainingStimulus.UPHILL_THRESHOLD:
        return _build_uphill_threshold(
            phase=phase,
            available_minutes=available_minutes,
        )

    if stimulus is TrainingStimulus.UPHILL_STRENGTH:
        return _build_uphill_strength(
            phase=phase,
            available_minutes=available_minutes,
        )

    if stimulus is TrainingStimulus.UPHILL_STRENGTH_ENDURANCE:
        return _build_uphill_strength_endurance(
            phase=phase,
            available_minutes=available_minutes,
        )

    if stimulus is TrainingStimulus.DOWNHILL_SPECIFICITY:
        return _build_downhill(
            available_minutes=available_minutes,
        )

    if stimulus in {
        TrainingStimulus.AEROBIC_EASY,
        TrainingStimulus.AEROBIC_ENDURANCE,
        TrainingStimulus.LONG_ENDURANCE,
        TrainingStimulus.RECOVERY,
        TrainingStimulus.RACE_SPECIFIC,
    }:
        return WorkStructure(
            structure_type=(
                WorkStructureType.CONTINUOUS
            ),
            stimulus=stimulus,
            available_minutes=available_minutes,
            continuous_minutes=available_minutes,
            description=(
                "Effort continu pendant "
                f"{available_minutes} min."
            ),
        )

    if stimulus in {
        TrainingStimulus.STRENGTH_LOWER_BODY,
        TrainingStimulus.STRENGTH_CORE,
    }:
        return WorkStructure(
            structure_type=(
                WorkStructureType.STRENGTH
            ),
            stimulus=stimulus,
            available_minutes=available_minutes,
            continuous_minutes=available_minutes,
            description=(
                "Bloc de renforcement contrôlé pendant "
                f"{available_minutes} min."
            ),
        )

    raise ValueError(
        "Aucune structure de travail n'est définie pour "
        f"'{stimulus.value}'."
    )


def _build_threshold(
    *,
    phase: TrainingPhase,
    available_minutes: int,
    phase_week_index: int,
) -> WorkStructure:
    if available_minutes < 16:
        return _continuous_quality(
            stimulus=TrainingStimulus.THRESHOLD,
            available_minutes=available_minutes,
            label="Seuil continu",
        )

    if phase in {
        TrainingPhase.FOUNDATION,
        TrainingPhase.BASE,
        TrainingPhase.RETURN_TO_TRAINING,
    }:
        candidates = (
            _minutes_interval(
                repetitions=3,
                work=6,
                recovery=2,
            ),
            _minutes_interval(
                repetitions=2,
                work=8,
                recovery=2,
            ),
        )

    elif phase is TrainingPhase.TAPER:
        if phase_week_index == 1:
            candidates = (
                _minutes_interval(
                    repetitions=3,
                    work=6,
                    recovery=2,
                ),
            )
        else:
            candidates = (
                _minutes_interval(
                    repetitions=2,
                    work=5,
                    recovery=2,
                ),
            )

    elif phase is TrainingPhase.BUILD:
        candidates = (
            _minutes_interval(
                repetitions=3,
                work=8,
                recovery=2,
            ),
            _minutes_interval(
                repetitions=3,
                work=10,
                recovery=2,
            ),
            _minutes_interval(
                repetitions=2,
                work=12,
                recovery=3,
            ),
        )

    else:
        candidates = (
            _minutes_interval(
                repetitions=3,
                work=10,
                recovery=2,
            ),
            _minutes_interval(
                repetitions=2,
                work=15,
                recovery=3,
            ),
            _minutes_interval(
                repetitions=3,
                work=12,
                recovery=2,
            ),
        )

    return _best_interval_structure(
        stimulus=TrainingStimulus.THRESHOLD,
        available_minutes=available_minutes,
        candidates=candidates,
        label="Travail au seuil",
    )

def _build_speed_development(
    *,
    available_minutes: int,
    phase_week_index: int,
) -> WorkStructure:
    """Construit un travail de vitesse courte en distance."""

    candidates = (
        (
            8,
            100,
            45,
        ),
        (
            8,
            200,
            60,
        ),
        (
            6,
            300,
            75,
        ),
        (
            6,
            400,
            90,
        ),
    )

    repetitions, distance_meters, recovery_seconds = (
        candidates[
            min(
                phase_week_index - 1,
                len(candidates) - 1,
            )
        ]
    )

    interval = WorkInterval(
        repetitions=repetitions,
        work_distance_meters=distance_meters,
        recovery_duration=recovery_seconds,
        recovery_unit=WorkDurationUnit.SECONDS,
    )

    estimated_work_seconds = (
        repetitions
        * _estimate_speed_repetition_seconds(
            distance_meters
        )
    )

    estimated_recovery_seconds = (
        max(
            repetitions - 1,
            0,
        )
        * recovery_seconds
    )

    estimated_total_seconds = (
        estimated_work_seconds
        + estimated_recovery_seconds
    )

    if estimated_total_seconds > available_minutes * 60:
        raise ValueError(
            "La structure de vitesse dépasse le temps disponible."
        )

    description = (
        f"{repetitions} × {distance_meters} m "
        f"/ récupération {recovery_seconds} s."
    )

    return WorkStructure(
        structure_type=WorkStructureType.REPEATS,
        stimulus=TrainingStimulus.SPEED_DEVELOPMENT,
        available_minutes=available_minutes,
        intervals=(
            interval,
        ),
        description=description,
    )


def _estimate_speed_repetition_seconds(
    distance_meters: int,
) -> int:
    """Estime conservativement la durée d'une répétition métrique.

    Cette estimation sert uniquement au contrôle du budget temporel.
    La cible exacte sera calculée ensuite à partir de la VMA.
    """

    if distance_meters <= 0:
        raise ValueError(
            "La distance doit être positive."
        )

    return max(
        1,
        round(
            distance_meters
            / 4.0
        ),
    )


def _build_vo2max(
    *,
    phase: TrainingPhase,
    available_minutes: int,
    phase_week_index: int,
) -> WorkStructure:
    if phase is TrainingPhase.BASE:
        base_candidates = (
            _seconds_interval(
                repetitions=10,
                work=60,
                recovery=60,
            ),
            _seconds_interval(
                repetitions=8,
                work=90,
                recovery=90,
            ),
            _minutes_interval(
                repetitions=5,
                work=3,
                recovery=2,
            ),
        )

        candidate = base_candidates[
            (phase_week_index - 1)
            % len(base_candidates)
        ]

        return _best_interval_structure(
            stimulus=TrainingStimulus.VO2MAX,
            available_minutes=available_minutes,
            candidates=(
                candidate,
            ),
            label="Intervalles VO2max",
        )

    if phase in {
        TrainingPhase.FOUNDATION,
        TrainingPhase.RETURN_TO_TRAINING,
    }:
        candidates = (
            _seconds_interval(
                repetitions=10,
                work=60,
                recovery=60,
            ),
            _seconds_interval(
                repetitions=8,
                work=90,
                recovery=90,
            ),
            _minutes_interval(
                repetitions=5,
                work=3,
                recovery=2,
            ),
        )

    else:
        candidates = (
            _seconds_interval(
                repetitions=8,
                work=90,
                recovery=60,
            ),
            _minutes_interval(
                repetitions=5,
                work=3,
                recovery=2,
            ),
            _minutes_interval(
                repetitions=5,
                work=4,
                recovery=2,
            ),
            _minutes_interval(
                repetitions=6,
                work=3,
                recovery=2,
            ),
        )

    return _best_interval_structure(
        stimulus=TrainingStimulus.VO2MAX,
        available_minutes=available_minutes,
        candidates=candidates,
        label="Intervalles VO2max",
    )


def _build_uphill_threshold(
    *,
    phase: TrainingPhase,
    available_minutes: int,
) -> WorkStructure:
    if phase in {
        TrainingPhase.FOUNDATION,
        TrainingPhase.BASE,
    }:
        candidates = (
            _minutes_interval(
                repetitions=4,
                work=4,
                recovery=2,
            ),
            _minutes_interval(
                repetitions=3,
                work=6,
                recovery=3,
            ),
        )

    else:
        candidates = (
            _minutes_interval(
                repetitions=4,
                work=5,
                recovery=3,
            ),
            _minutes_interval(
                repetitions=3,
                work=8,
                recovery=3,
            ),
            _minutes_interval(
                repetitions=3,
                work=10,
                recovery=4,
            ),
        )

    return _best_interval_structure(
        stimulus=TrainingStimulus.UPHILL_THRESHOLD,
        available_minutes=available_minutes,
        candidates=candidates,
        label="Montées soutenues",
    )


def _build_uphill_strength(
    *,
    phase: TrainingPhase,
    available_minutes: int,
) -> WorkStructure:
    del phase

    candidates = (
        _seconds_interval(
            repetitions=10,
            work=30,
            recovery=60,
        ),
        _seconds_interval(
            repetitions=10,
            work=45,
            recovery=75,
        ),
        _seconds_interval(
            repetitions=8,
            work=60,
            recovery=90,
        ),
        _minutes_interval(
            repetitions=6,
            work=2,
            recovery=2,
        ),
    )

    return _best_interval_structure(
        stimulus=TrainingStimulus.UPHILL_STRENGTH,
        available_minutes=available_minutes,
        candidates=candidates,
        label="Répétitions de force en montée",
        structure_type=WorkStructureType.REPEATS,
    )


def _build_uphill_strength_endurance(
    *,
    phase: TrainingPhase,
    available_minutes: int,
) -> WorkStructure:
    """Construit un circuit de force-endurance en côte.

    Le circuit associe une pré-fatigue isométrique, une course en
    montée et une récupération active en descente.

    BUILD utilise la variante courte :
    1 min chaise + 45 s côte + 1 min descente.

    SPECIFIC utilise la variante longue :
    1 min chaise + 1 min côte + 1 min 30 descente.
    """

    if phase is TrainingPhase.SPECIFIC:
        work_seconds = 60
        recovery_seconds = 90
    else:
        work_seconds = 45
        recovery_seconds = 60

    steps = (
        CircuitStep(
            step_type=CircuitStepType.STRENGTH,
            duration_seconds=60,
            description="Chaise isométrique",
        ),
        CircuitStep(
            step_type=CircuitStepType.WORK,
            duration_seconds=work_seconds,
            description="Course en côte",
        ),
        CircuitStep(
            step_type=CircuitStepType.RECOVERY,
            duration_seconds=recovery_seconds,
            description="Récupération active en descente",
        ),
    )

    cycle_duration_seconds = sum(
        step.duration_seconds
        for step in steps
    )

    available_seconds = (
        available_minutes
        * 60
    )

    repetitions = (
        available_seconds
        // cycle_duration_seconds
    )

    if repetitions < 2:
        return _continuous_quality(
            stimulus=(
                TrainingStimulus.UPHILL_STRENGTH_ENDURANCE
            ),
            available_minutes=available_minutes,
            label="Force-endurance en côte",
        )

    circuit = WorkCircuit(
        repetitions=repetitions,
        steps=steps,
    )

    description = (
        f"{circuit.repetitions} × "
        "1 min chaise isométrique + "
        f"{work_seconds} s course en côte + "
        f"{recovery_seconds} s récupération "
        "active en descente."
    )

    return WorkStructure(
        structure_type=WorkStructureType.CIRCUIT,
        stimulus=(
            TrainingStimulus.UPHILL_STRENGTH_ENDURANCE
        ),
        available_minutes=available_minutes,
        circuit=circuit,
        description=description,
    )


def _build_downhill(
    *,
    available_minutes: int,
) -> WorkStructure:
    candidates = (
        _minutes_interval(
            repetitions=4,
            work=3,
            recovery=3,
        ),
        _minutes_interval(
            repetitions=5,
            work=3,
            recovery=3,
        ),
        _minutes_interval(
            repetitions=4,
            work=5,
            recovery=4,
        ),
    )

    return _best_interval_structure(
        stimulus=TrainingStimulus.DOWNHILL_SPECIFICITY,
        available_minutes=available_minutes,
        candidates=candidates,
        label="Descentes techniques",
        structure_type=WorkStructureType.TECHNICAL,
    )


def _continuous_quality(
    *,
    stimulus: TrainingStimulus,
    available_minutes: int,
    label: str,
) -> WorkStructure:
    return WorkStructure(
        structure_type=(
            WorkStructureType.CONTINUOUS
        ),
        stimulus=stimulus,
        available_minutes=available_minutes,
        continuous_minutes=available_minutes,
        description=(
            f"{label} pendant "
            f"{available_minutes} min."
        ),
    )


def _fit_interval_to_available_time(
    *,
    interval: WorkInterval,
    available_seconds: int,
    minimum_repetitions: int = 2,
) -> WorkInterval | None:
    """Réduit uniquement le nombre de répétitions pour tenir dans le temps."""

    for repetitions in range(
        interval.repetitions,
        minimum_repetitions - 1,
        -1,
    ):
        candidate = WorkInterval(
            repetitions=repetitions,
            work_duration=interval.work_duration,
            work_unit=interval.work_unit,
            recovery_duration=interval.recovery_duration,
            recovery_unit=interval.recovery_unit,
        )

        if (
            candidate.total_duration_seconds
            <= available_seconds
        ):
            return candidate

    return None


def _best_interval_structure(
    *,
    stimulus: TrainingStimulus,
    available_minutes: int,
    candidates: tuple[
        WorkInterval,
        ...,
    ],
    label: str,
    structure_type: WorkStructureType = (
        WorkStructureType.INTERVALS
    ),
) -> WorkStructure:
    available_seconds = (
        available_minutes
        * 60
    )

    compatible = tuple(
        candidate
        for candidate in candidates
        if (
            candidate.total_duration_seconds
            <= available_seconds
        )
    )

    if not compatible:
        fitted = tuple(
            candidate
            for candidate in (
                _fit_interval_to_available_time(
                    interval=source,
                    available_seconds=available_seconds,
                )
                for source in candidates
            )
            if candidate is not None
        )

        if fitted:
            compatible = fitted
        else:
            return _continuous_quality(
                stimulus=stimulus,
                available_minutes=available_minutes,
                label=label,
            )

    selected = max(
        compatible,
        key=lambda item: (
            item.total_work_seconds,
            item.total_duration_seconds,
        ),
    )

    description = (
        _format_interval_description(
            selected
        )
    )

    return WorkStructure(
        structure_type=structure_type,
        stimulus=stimulus,
        available_minutes=available_minutes,
        intervals=(
            selected,
        ),
        description=description,
    )


def _minutes_interval(
    *,
    repetitions: int,
    work: int,
    recovery: int,
) -> WorkInterval:
    return WorkInterval(
        repetitions=repetitions,
        work_duration=work,
        work_unit=WorkDurationUnit.MINUTES,
        recovery_duration=recovery,
        recovery_unit=WorkDurationUnit.MINUTES,
    )


def _seconds_interval(
    *,
    repetitions: int,
    work: int,
    recovery: int,
) -> WorkInterval:
    return WorkInterval(
        repetitions=repetitions,
        work_duration=work,
        work_unit=WorkDurationUnit.SECONDS,
        recovery_duration=recovery,
        recovery_unit=WorkDurationUnit.SECONDS,
    )


def _duration_to_seconds(
    *,
    value: int,
    unit: WorkDurationUnit,
) -> int:
    if unit is WorkDurationUnit.SECONDS:
        return value

    return (
        value
        * 60
    )


def _format_interval_description(
    interval: WorkInterval,
) -> str:
    work = _format_duration(
        interval.work_duration,
        interval.work_unit,
    )

    recovery = ""

    if interval.recovery_duration is not None:
        assert interval.recovery_unit is not None

        recovery = (
            " / récupération "
            + _format_duration(
                interval.recovery_duration,
                interval.recovery_unit,
            )
        )

    return (
        f"{interval.repetitions} × "
        f"{work}"
        f"{recovery}."
    )


def _format_duration(
    value: int,
    unit: WorkDurationUnit,
) -> str:
    if unit is WorkDurationUnit.SECONDS:
        return (
            f"{value} s"
        )

    return (
        f"{value} min"
    )
