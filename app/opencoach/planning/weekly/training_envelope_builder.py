"""Construction de l'enveloppe hebdomadaire OpenCoach.

Ce module assemble les décisions déterministes déjà calculées :
- phase ;
- charge ;
- récupération ;
- disponibilités ;
- capacité temporelle ;
- prescription des stimuli ;
- demande quantitative de stimuli ;
- intentions de séance ;
- placement hebdomadaire.

Il ne génère aucune séance concrète.

Le pipeline repose exclusivement sur les intentions de séance.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, timedelta

from opencoach.planning.stimulus.contextual_prescription import (
    ContextualStimulusPrescription,
)
from opencoach.planning.trajectory.load_recovery_cycle import (
    LoadRecoveryDecision,
)
from opencoach.planning.trajectory.multi_week import (
    TrajectoryWeekType,
)
from opencoach.planning.sessions.intent import (
    build_session_intent,
)
from opencoach.planning.sessions.intent_builder import (
    SessionIntentPlan,
    build_session_intent_plan,
    complete_session_intent_frequency,
)
from opencoach.planning.weekly.load_progression import (
    WeeklyLoadTarget,
)
from opencoach.planning.stimulus.training import (
    SpecificityLevel,
    StimulusLoadCategory,
    StimulusPriority,
    SubstitutionPolicy,
    TrainingModality,
    TrainingStimulus,
    TrainingStimulusRequirement,
)
from opencoach.planning.weekly.schedule_capacity import (
    DayScheduleCapacity,
)
from opencoach.planning.weekly.schedule_types import (
    Weekday,
)
from opencoach.planning.weekly.session_intent_scheduler import (
    WeeklySessionIntentSchedule,
    schedule_session_intents,
)
from opencoach.planning.stimulus.weekly_demand import (
    build_weekly_stimulus_demand,
)
from opencoach.planning.weekly.training_envelope import (
    SchedulePressure,
    TrainingPhase,
    WeeklyTrainingEnvelope,
)


@dataclass(frozen=True, slots=True)
class WeeklyTrainingEnvelopeInput:
    """Données nécessaires à la construction d'une enveloppe."""

    week_start: date

    phase: TrainingPhase

    load_target: WeeklyLoadTarget

    recovery: LoadRecoveryDecision

    prescription: ContextualStimulusPrescription

    available_days: tuple[
        Weekday,
        ...
    ]

    target_race_date: date | None = None

    reserved_race_dates: tuple[
        date,
        ...
    ] = ()

    race_protection_dates: tuple[
        date,
        ...
    ] = ()

    race_recovery_dates: tuple[
        date,
        ...
    ] = ()

    phase_week_index: int = 1

    target_session_count: int | None = None

    reference_weekly_duration_minutes: float | None = None

    target_weekly_duration_minutes: float | None = None

    long_endurance_reference_minutes: float | None = None

    day_capacities: tuple[
        DayScheduleCapacity,
        ...
    ] = ()

    athlete_schedule_constrained: bool = False


@dataclass(frozen=True, slots=True)
class _AdjustedLoads:
    """Charges finales transmises à l'enveloppe."""

    target_load: float
    load_min: float
    load_max: float


def build_weekly_training_envelope(
    *,
    input_data: WeeklyTrainingEnvelopeInput,
) -> WeeklyTrainingEnvelope:
    """Construit l'enveloppe hebdomadaire complète."""

    week_end = (
        input_data.week_start
        + timedelta(days=6)
    )

    effective_available_days = (
        _exclude_reserved_race_days(
            week_start=input_data.week_start,
            available_days=input_data.available_days,
            target_race_date=input_data.target_race_date,
            reserved_race_dates=(
                input_data.reserved_race_dates
            ),
        )
    )

    adjusted_loads = _apply_recovery_factor(
        load_target=input_data.load_target,
        recovery=input_data.recovery,
    )

    week_type = _resolve_week_type(
        phase=input_data.phase,
        recovery=input_data.recovery,
        target_load=adjusted_loads.target_load,
    )

    weekly_demand = (
        build_weekly_stimulus_demand(
            prescription=input_data.prescription,
            week_type=week_type,
            target_load=adjusted_loads.target_load,
            reference_load=(
                input_data.load_target.theoretical_load
            ),
            phase_week_index=(
                input_data.phase_week_index
            ),
            maintenance_mode=(
                input_data.target_race_date
                is None
            ),
        )
    )

    intent_plan = build_session_intent_plan(
        weekly_demand=weekly_demand,
    )

    intent_plan = _inject_pre_race_activation(
        plan=intent_plan,
        week_start=input_data.week_start,
        available_days=(
            effective_available_days
        ),
        reserved_race_dates=(
            input_data.reserved_race_dates
        ),
        protection_dates=(
            input_data.race_protection_dates
        ),
    )

    effective_target_session_count = (
        min(
            input_data.target_session_count,
            len(
                set(
                    effective_available_days
                )
            ),
        )
        if input_data.target_session_count
        is not None
        else None
    )

    if (
        adjusted_loads.target_load > 0
        and effective_target_session_count
        is not None
    ):
        intent_plan = (
            complete_session_intent_frequency(
                plan=intent_plan,
                target_session_count=(
                    effective_target_session_count
                ),
            )
        )

    effective_day_capacities = (
        _apply_race_protection(
            week_start=input_data.week_start,
            available_days=(
                effective_available_days
            ),
            day_capacities=(
                input_data.day_capacities
            ),
            protection_dates=(
                input_data.race_protection_dates
            ),
        )
    )

    effective_day_capacities = (
        _apply_post_race_recovery(
            week_start=input_data.week_start,
            available_days=(
                effective_available_days
            ),
            day_capacities=(
                effective_day_capacities
            ),
            recovery_dates=(
                input_data.race_recovery_dates
            ),
        )
    )

    session_schedule = (
        schedule_session_intents(
            plan=intent_plan,
            available_days=(
                effective_available_days
            ),
            day_capacities=(
                effective_day_capacities
            ),
        )
    )

    schedule_pressure = (
        _classify_schedule_pressure(
            schedule=session_schedule,
            available_days=(
                effective_available_days
            ),
        )
    )

    notes = _build_notes(
        schedule=session_schedule,
        recovery=input_data.recovery,
    )

    return WeeklyTrainingEnvelope(
        week_start=input_data.week_start,
        week_end=week_end,
        phase=input_data.phase,
        phase_week_index=(
            input_data.phase_week_index
        ),
        target_load=adjusted_loads.target_load,
        reference_duration_minutes=(
            input_data.reference_weekly_duration_minutes
        ),
        target_duration_minutes=(
            input_data.target_weekly_duration_minutes
            if input_data.target_weekly_duration_minutes
            is not None
            else _resolve_target_duration_minutes(
                reference_duration_minutes=(
                    input_data.reference_weekly_duration_minutes
                ),
                recovery=input_data.recovery,
                target_load=(
                    adjusted_loads.target_load
                ),
            )
        ),
        long_endurance_reference_minutes=(
            input_data.long_endurance_reference_minutes
        ),
        load_min=adjusted_loads.load_min,
        load_max=adjusted_loads.load_max,
        available_days=effective_available_days,
        session_slots=session_schedule.slots,
        schedule_pressure=schedule_pressure,
        athlete_schedule_constrained=(
            input_data.athlete_schedule_constrained
            or session_schedule.constrained
        ),
        notes=notes,
    )


def _apply_recovery_factor(
    *,
    load_target: WeeklyLoadTarget,
    recovery: LoadRecoveryDecision,
) -> _AdjustedLoads:
    factor = recovery.load_factor

    return _AdjustedLoads(
        target_load=(
            load_target.target_load
            * factor
        ),
        load_min=(
            load_target.load_min
            * factor
        ),
        load_max=(
            load_target.load_max
            * factor
        ),
    )


def _resolve_week_type(
    *,
    phase: TrainingPhase,
    recovery: LoadRecoveryDecision,
    target_load: float,
) -> TrajectoryWeekType:
    """Déduit le rôle qualitatif de la semaine."""

    if target_load == 0:
        return (
            TrajectoryWeekType.SUSPENDED
        )

    if (
        phase
        is TrainingPhase.RETURN_TO_TRAINING
    ):
        return (
            TrajectoryWeekType.RETURN_TO_TRAINING
        )

    if recovery.recovery_week:
        return (
            TrajectoryWeekType.RECOVERY
        )

    if phase is TrainingPhase.TAPER:
        return TrajectoryWeekType.TAPER

    return TrajectoryWeekType.LOADING


def _classify_schedule_pressure(
    *,
    schedule: WeeklySessionIntentSchedule,
    available_days: tuple[
        Weekday,
        ...
    ],
) -> SchedulePressure:
    unique_available_days = len(
        set(available_days)
    )

    if schedule.constrained:
        return SchedulePressure.HIGH

    if unique_available_days <= 2:
        return SchedulePressure.HIGH

    if unique_available_days <= 4:
        return SchedulePressure.MODERATE

    return SchedulePressure.LOW


def _build_notes(
    *,
    schedule: WeeklySessionIntentSchedule,
    recovery: LoadRecoveryDecision,
) -> tuple[
    str,
    ...
]:
    notes: list[
        str
    ] = []

    if recovery.recovery_week:
        notes.append(
            "Semaine de récupération : la charge globale "
            "et la densité qualitative ont été réduites "
            "par le moteur."
        )

    if schedule.constrained:
        notes.append(
            "Les disponibilités ou capacités temporelles "
            "ne permettent pas de positionner toutes les "
            "intentions de séance souhaitées."
        )

    if schedule.omitted_intents:
        required_omitted = tuple(
            intent
            for intent in schedule.omitted_intents
            if intent.required
        )

        optional_omitted = tuple(
            intent
            for intent in schedule.omitted_intents
            if not intent.required
        )

        if required_omitted:
            omitted = ", ".join(
                intent.primary_stimulus.value
                for intent in required_omitted
            )

            notes.append(
                "Intentions obligatoires non positionnées : "
                f"{omitted}."
            )

        if optional_omitted:
            omitted = ", ".join(
                intent.primary_stimulus.value
                for intent in optional_omitted
            )

            notes.append(
                "Intentions optionnelles non positionnées : "
                f"{omitted}."
            )

    return tuple(
        notes
    )

def _resolve_target_duration_minutes(
    *,
    reference_duration_minutes: float | None,
    recovery: LoadRecoveryDecision,
    target_load: float,
) -> float | None:
    """Calcule le budget temporel hebdomadaire.

    La fréquence est conservée ; une récupération planifiée réduit
    principalement le volume total et la densité qualitative.

    Les règles propres au taper seront affinées séparément.
    """

    if reference_duration_minutes is None:
        return None

    if target_load <= 0:
        return None

    factor = (
        recovery.load_factor
        if recovery.recovery_week
        else 1.0
    )

    return round(
        reference_duration_minutes
        * factor,
        1,
    )


_WEEKDAY_INDEX = {
    Weekday.MONDAY: 0,
    Weekday.TUESDAY: 1,
    Weekday.WEDNESDAY: 2,
    Weekday.THURSDAY: 3,
    Weekday.FRIDAY: 4,
    Weekday.SATURDAY: 5,
    Weekday.SUNDAY: 6,
}



def _exclude_reserved_race_days(
    *,
    week_start: date,
    available_days: tuple[
        Weekday,
        ...
    ],
    target_race_date: date | None,
    reserved_race_dates: tuple[
        date,
        ...
    ],
) -> tuple[
    Weekday,
    ...
]:
    """Réserve les jours de compétition de la semaine.

    La course principale et les courses préparatoires sont des
    événements déjà définis dans le calendrier. Le générateur
    d'entraînement ne doit jamais placer une séance supplémentaire
    sur ces journées.
    """

    week_end = (
        week_start
        + timedelta(days=6)
    )

    race_dates = set(
        reserved_race_dates
    )

    if target_race_date is not None:
        race_dates.add(
            target_race_date
        )

    reserved_weekday_indexes = {
        race_date.weekday()
        for race_date in race_dates
        if (
            week_start
            <= race_date
            <= week_end
        )
    }

    if not reserved_weekday_indexes:
        return available_days

    return tuple(
        day
        for day in available_days
        if (
            _WEEKDAY_INDEX[day]
            not in reserved_weekday_indexes
        )
    )


def _apply_race_protection(
    *,
    week_start: date,
    available_days: tuple[
        Weekday,
        ...
    ],
    day_capacities: tuple[
        DayScheduleCapacity,
        ...
    ],
    protection_dates: tuple[
        date,
        ...
    ],
) -> tuple[
    DayScheduleCapacity,
    ...
]:
    """Bloque qualité et force sur les jours protégés avant course."""

    week_end = (
        week_start
        + timedelta(days=6)
    )

    protected_indexes = {
        protected_date.weekday()
        for protected_date in protection_dates
        if (
            week_start
            <= protected_date
            <= week_end
        )
    }

    provided = {
        capacity.day: capacity
        for capacity in day_capacities
    }

    result: list[
        DayScheduleCapacity
    ] = []

    for day in available_days:
        existing = provided.get(
            day
        )

        max_duration = (
            existing.max_duration_minutes
            if existing is not None
            else None
        )

        blocked = (
            existing.blocked_load_categories
            if existing is not None
            else frozenset()
        )

        if (
            _WEEKDAY_INDEX[day]
            in protected_indexes
        ):
            blocked = (
                blocked
                | frozenset(
                    {
                        StimulusLoadCategory.QUALITY,
                        StimulusLoadCategory.STRENGTH,
                    }
                )
            )

        result.append(
            DayScheduleCapacity(
                day=day,
                max_duration_minutes=(
                    max_duration
                ),
                blocked_load_categories=(
                    blocked
                ),
            )
        )

    return tuple(
        result
    )


def _inject_pre_race_activation(
    *,
    plan: SessionIntentPlan,
    week_start: date,
    available_days: tuple[
        Weekday,
        ...
    ],
    reserved_race_dates: tuple[
        date,
        ...
    ],
    protection_dates: tuple[
        date,
        ...
    ],
) -> SessionIntentPlan:
    """Ajoute une activation avant une course préparatoire exigeante.

    La présence d'une fenêtre de protection avant la course indique
    que son impact est suffisant pour justifier une adaptation.

    Placement autorisé :
    - J-2 en priorité ;
    - J-1 en solution de repli.

    Lorsque ces deux journées sont indisponibles, aucune activation
    artificielle n'est ajoutée ailleurs dans la semaine.
    """

    week_end = (
        week_start
        + timedelta(days=6)
    )

    available = set(
        available_days
    )

    protected_dates = set(
        protection_dates
    )

    qualifying_races = tuple(
        sorted(
            race_date
            for race_date in reserved_race_dates
            if (
                week_start
                <= race_date
                <= week_end
                and any(
                    protected_date
                    < race_date
                    for protected_date
                    in protected_dates
                )
            )
        )
    )

    if not qualifying_races:
        return plan

    intents = list(
        plan.intents
    )

    represented = list(
        plan.represented_stimuli
    )

    for race_date in qualifying_races:
        candidate_dates = (
            race_date
            - timedelta(days=2),
            race_date
            - timedelta(days=1),
        )

        candidate_days: list[
            Weekday
        ] = []

        for candidate_date in candidate_dates:
            if not (
                week_start
                <= candidate_date
                <= week_end
            ):
                continue

            day = _weekday_from_date(
                candidate_date
            )

            if day not in available:
                continue

            candidate_days.append(
                day
            )

        if not candidate_days:
            continue

        requirement = (
            TrainingStimulusRequirement(
                stimulus=(
                    TrainingStimulus
                    .PRE_RACE_ACTIVATION
                ),
                priority=(
                    StimulusPriority.SUPPORT
                ),
                specificity=(
                    SpecificityLevel.MODERATE
                ),
                substitution=(
                    SubstitutionPolicy.ALLOWED
                ),
                preferred_modalities=(
                    TrainingModality.RUNNING,
                    TrainingModality.TRAIL_RUNNING,
                ),
                duration_min_minutes=20,
                duration_max_minutes=30,
            )
        )

        activation = (
            build_session_intent(
                primary=requirement,
            )
        )

        allowed_days = tuple(
            day.value
            for day in candidate_days
        )

        activation = replace(
            activation,
            preferred_days=allowed_days,
            allowed_days=allowed_days,
            required=False,
        )

        intents.append(
            activation
        )

        if (
            TrainingStimulus
            .PRE_RACE_ACTIVATION
            not in represented
        ):
            represented.append(
                TrainingStimulus
                .PRE_RACE_ACTIVATION
            )

    return SessionIntentPlan(
        intents=tuple(
            intents
        ),
        source_demand=(
            plan.source_demand
        ),
        represented_stimuli=tuple(
            represented
        ),
        unrepresented_stimuli=(
            plan.unrepresented_stimuli
        ),
    )


def _weekday_from_date(
    value: date,
) -> Weekday:
    """Convertit un weekday Python vers le type OpenCoach."""

    mapping = {
        0: Weekday.MONDAY,
        1: Weekday.TUESDAY,
        2: Weekday.WEDNESDAY,
        3: Weekday.THURSDAY,
        4: Weekday.FRIDAY,
        5: Weekday.SATURDAY,
        6: Weekday.SUNDAY,
    }

    return mapping[
        value.weekday()
    ]


def _apply_post_race_recovery(
    *,
    week_start: date,
    available_days: tuple[
        Weekday,
        ...
    ],
    day_capacities: tuple[
        DayScheduleCapacity,
        ...
    ],
    recovery_dates: tuple[
        date,
        ...
    ],
) -> tuple[
    DayScheduleCapacity,
    ...
]:
    """Applique une reprise progressive après une course exigeante.

    Politique déterministe :

    J+1 / J+2
        SUPPORT uniquement.
        Durée maximale recommandée : 30 minutes.

    J+3 / J+4
        SUPPORT et ENDURANCE autorisés.
        QUALITY et STRENGTH restent bloqués.
        Durée maximale : 45 minutes.

    J+5 / J+6
        SUPPORT et ENDURANCE autorisés.
        QUALITY et STRENGTH restent bloqués.
        Durée maximale : 60 minutes.

    Après la fenêtre de récupération, les contraintes spécifiques
    à la course disparaissent.

    Les capacités déjà définies par l'athlète restent prioritaires :
    cette fonction ne peut jamais augmenter une durée disponible.
    """

    recovery_stage_by_date = (
        _build_post_race_recovery_stages(
            recovery_dates
        )
    )

    provided = {
        capacity.day: capacity
        for capacity in day_capacities
    }

    result: list[
        DayScheduleCapacity
    ] = []

    for day in available_days:
        existing = provided.get(
            day
        )

        max_duration = (
            existing.max_duration_minutes
            if existing is not None
            else None
        )

        blocked = (
            existing.blocked_load_categories
            if existing is not None
            else frozenset()
        )

        current_date = (
            week_start
            + timedelta(
                days=_WEEKDAY_INDEX[
                    day
                ]
            )
        )

        recovery_day = (
            recovery_stage_by_date.get(
                current_date
            )
        )

        if recovery_day is not None:
            if recovery_day <= 2:
                blocked = (
                    blocked
                    | frozenset(
                        {
                            StimulusLoadCategory.ENDURANCE,
                            StimulusLoadCategory.QUALITY,
                            StimulusLoadCategory.STRENGTH,
                        }
                    )
                )

                max_duration = (
                    _restrict_duration(
                        current=max_duration,
                        recovery_limit=30,
                    )
                )

            elif recovery_day <= 4:
                blocked = (
                    blocked
                    | frozenset(
                        {
                            StimulusLoadCategory.QUALITY,
                            StimulusLoadCategory.STRENGTH,
                        }
                    )
                )

                max_duration = (
                    _restrict_duration(
                        current=max_duration,
                        recovery_limit=45,
                    )
                )

            else:
                blocked = (
                    blocked
                    | frozenset(
                        {
                            StimulusLoadCategory.QUALITY,
                            StimulusLoadCategory.STRENGTH,
                        }
                    )
                )

                max_duration = (
                    _restrict_duration(
                        current=max_duration,
                        recovery_limit=60,
                    )
                )

        result.append(
            DayScheduleCapacity(
                day=day,
                max_duration_minutes=(
                    max_duration
                ),
                blocked_load_categories=(
                    blocked
                ),
            )
        )

    return tuple(
        result
    )


def _build_post_race_recovery_stages(
    recovery_dates: tuple[
        date,
        ...
    ],
) -> dict[
    date,
    int,
]:
    """Numérote J+1, J+2... dans chaque fenêtre continue.

    Plusieurs courses peuvent exister dans le calendrier. Les dates
    consécutives constituent une même fenêtre ; une rupture redémarre
    une nouvelle séquence à J+1.
    """

    ordered_dates = tuple(
        sorted(
            set(
                recovery_dates
            )
        )
    )

    result: dict[
        date,
        int,
    ] = {}

    previous_date: date | None = None
    recovery_day = 0

    for current_date in ordered_dates:
        if (
            previous_date is None
            or current_date
            != previous_date
            + timedelta(days=1)
        ):
            recovery_day = 1
        else:
            recovery_day += 1

        result[
            current_date
        ] = recovery_day

        previous_date = current_date

    return result


def _restrict_duration(
    *,
    current: int | None,
    recovery_limit: int,
) -> int:
    """Applique un plafond sans augmenter une capacité existante."""

    if current is None:
        return recovery_limit

    return min(
        current,
        recovery_limit,
    )
