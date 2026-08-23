from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal
from uuid import UUID


MacrocyclePhaseType = Literal[
    "foundation",
    "base",
    "build",
    "specific",
    "taper",
    "recovery",
    "race",
]

TrainingStimulusType = Literal[
    "aerobic_endurance",
    "long_endurance",
    "threshold",
    "vo2max",
    "race_specific",
    "hill_strength",
    "downhill_skill",
    "strength",
    "recovery",
    "physiological_assessment",
]

TrajectoryStatus = Literal[
    "planned",
    "active",
    "completed",
    "revised",
]

StrategyRevisionReason = Literal[
    "initial_plan",
    "new_race",
    "race_changed",
    "injury",
    "availability_change",
    "training_response",
    "extended_interruption",
    "physiological_update",
    "manual_request",
    "other",
]


@dataclass(frozen=True)
class TrainingStimulus:
    """Intention physiologique à développer, sans imposer de séance."""

    stimulus_type: TrainingStimulusType

    priority: Literal[
        "low",
        "medium",
        "high",
    ]

    target_exposure_minutes: int | None = None

    notes: str | None = None


@dataclass(frozen=True)
class WeekTrajectory:
    """Enveloppe stratégique d'une semaine future."""

    week_number: int

    start_date: date
    end_date: date

    phase: MacrocyclePhaseType

    target_load: float | None
    load_min: float | None
    load_max: float | None

    target_duration_minutes: int | None
    target_distance_km: float | None
    target_elevation_gain_m: float | None

    primary_stimuli: tuple[
        TrainingStimulus,
        ...
    ]

    recovery_week: bool = False

    status: TrajectoryStatus = "planned"

    notes: str | None = None

    def __post_init__(self) -> None:
        if self.week_number < 1:
            raise ValueError(
                "Le numéro de semaine doit être supérieur ou égal à 1."
            )

        if self.end_date < self.start_date:
            raise ValueError(
                "La fin de semaine ne peut pas précéder son début."
            )

        if (
            self.load_min is not None
            and self.load_max is not None
            and self.load_min > self.load_max
        ):
            raise ValueError(
                "La charge minimale ne peut pas dépasser "
                "la charge maximale."
            )

        if (
            self.target_load is not None
            and self.load_min is not None
            and self.target_load < self.load_min
        ):
            raise ValueError(
                "La charge cible doit appartenir à son enveloppe."
            )

        if (
            self.target_load is not None
            and self.load_max is not None
            and self.target_load > self.load_max
        ):
            raise ValueError(
                "La charge cible doit appartenir à son enveloppe."
            )


@dataclass(frozen=True)
class MacrocyclePhase:
    """Période stratégique du macrocycle."""

    phase_type: MacrocyclePhaseType

    start_date: date
    end_date: date

    objective: str

    primary_stimuli: tuple[
        TrainingStimulusType,
        ...
    ]

    def __post_init__(self) -> None:
        if self.end_date < self.start_date:
            raise ValueError(
                "La fin de phase ne peut pas précéder son début."
            )


@dataclass(frozen=True)
class StrategyRevision:
    """Trace expliquant pourquoi une stratégie a été créée ou révisée."""

    reason: StrategyRevisionReason

    created_at: datetime

    description: str

    previous_strategy_id: UUID | None = None


@dataclass(frozen=True)
class SeasonStrategy:
    """Vision stratégique jusqu'à l'objectif principal.

    Elle décrit la trajectoire recherchée mais ne contient pas
    les séances détaillées des semaines futures.
    """

    id: UUID

    athlete_profile_id: UUID

    planning_date: date

    target_race_id: UUID
    target_race_date: date

    phases: tuple[
        MacrocyclePhase,
        ...
    ]

    weeks: tuple[
        WeekTrajectory,
        ...
    ]

    revision: StrategyRevision

    knowledge_version: str
    policy_version: str

    created_at: datetime

    @property
    def weeks_to_goal(self) -> int:
        """Nombre de semaines calendaires entre planification et objectif."""

        days = (
            self.target_race_date
            - self.planning_date
        ).days

        if days <= 0:
            return 0

        return (
            days + 6
        ) // 7

    @property
    def current_week(
        self,
    ) -> WeekTrajectory | None:
        """Retourne la trajectoire contenant la date de planification."""

        return next(
            (
                week
                for week in self.weeks
                if (
                    week.start_date
                    <= self.planning_date
                    <= week.end_date
                )
            ),
            None,
        )
