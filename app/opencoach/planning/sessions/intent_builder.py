"""Construction déterministe des intentions de séance hebdomadaires.

Ce module transforme une WeeklyStimulusDemand en intentions de séance.

Il décide :
- quels stimuli doivent être représentés ;
- quels stimuli peuvent être regroupés dans une même intention ;
- quels stimuli doivent rester séparés.

Il ne décide pas :
- des jours ;
- des exercices ;
- des intervalles ;
- des allures ;
- du contenu concret des séances.

Ces décisions appartiennent aux étapes ultérieures du moteur
et au moteur de génération des séances.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from opencoach.planning.sessions.intent import (
    SessionIntent,
    build_session_intent,
)
from opencoach.planning.stimulus.training import (
    StimulusPriority,
    TrainingModality,
    TrainingStimulus,
    TrainingStimulusRequirement,
)
from opencoach.planning.stimulus.weekly_demand import (
    StimulusDemand,
    WeeklyStimulusDemand,
)


_TRAIL_LONG_SESSION_SECONDARY_STIMULI = {
    TrainingStimulus.UPHILL_STRENGTH,
    TrainingStimulus.DOWNHILL_SPECIFICITY,
    TrainingStimulus.RACE_SPECIFIC,
}


@dataclass(frozen=True, slots=True)
class SessionIntentPlan:
    """Résultat de la construction des intentions de séance."""

    intents: tuple[
        SessionIntent,
        ...
    ]

    source_demand: WeeklyStimulusDemand

    represented_stimuli: tuple[
        TrainingStimulus,
        ...
    ]

    unrepresented_stimuli: tuple[
        TrainingStimulus,
        ...
    ]

    @property
    def session_count(self) -> int:
        """Nombre d'intentions de séance produites."""

        return len(
            self.intents
        )


def build_session_intent_plan(
    *,
    weekly_demand: WeeklyStimulusDemand,
) -> SessionIntentPlan:
    """Construit les intentions de séance d'une semaine."""

    active_demands = tuple(
        demand
        for demand in weekly_demand.demands
        if demand.target_occurrences > 0
    )

    if not active_demands:
        return SessionIntentPlan(
            intents=(),
            source_demand=weekly_demand,
            represented_stimuli=(),
            unrepresented_stimuli=(),
        )

    remaining = list(
        active_demands
    )

    intents: list[
        SessionIntent
    ] = []

    represented: list[
        TrainingStimulus
    ] = []

    _build_uphill_strength_alternative_intent(
        remaining=remaining,
        intents=intents,
        represented=represented,
    )

    _build_long_endurance_intents(
        remaining=remaining,
        intents=intents,
        represented=represented,
    )

    _build_separate_key_intents(
        remaining=remaining,
        intents=intents,
        represented=represented,
    )

    _build_strength_intents(
        remaining=remaining,
        intents=intents,
        represented=represented,
    )

    _build_remaining_intents(
        remaining=remaining,
        intents=intents,
        represented=represented,
    )

    all_active_stimuli = tuple(
        demand.stimulus
        for demand in active_demands
    )

    unrepresented = tuple(
        stimulus
        for stimulus in all_active_stimuli
        if stimulus not in represented
    )

    return SessionIntentPlan(
        intents=tuple(
            intents
        ),
        source_demand=weekly_demand,
        represented_stimuli=tuple(
            represented
        ),
        unrepresented_stimuli=unrepresented,
    )


def _build_uphill_strength_alternative_intent(
    *,
    remaining: list[
        StimulusDemand
    ],
    intents: list[
        SessionIntent
    ],
    represented: list[
        TrainingStimulus
    ],
) -> None:
    """Regroupe les deux variantes de force en côte.

    Lorsque la force en côte classique et la force-endurance
    sont toutes les deux demandées, elles représentent un même
    besoin physiologique principal.

    La variante force-endurance devient alors le stimulus
    principal de l'intention, tandis que la force en côte
    classique est considérée comme couverte secondairement.

    Cette règle évite de créer deux séances lourdes distinctes.
    """

    classic = _find_demand(
        remaining,
        TrainingStimulus.UPHILL_STRENGTH,
    )

    endurance = _find_demand(
        remaining,
        TrainingStimulus.UPHILL_STRENGTH_ENDURANCE,
    )

    if (
        classic is None
        or endurance is None
    ):
        return

    if (
        classic.target_occurrences <= 0
        or endurance.target_occurrences <= 0
    ):
        return

    if not _can_share_session(
        primary=endurance.requirement,
        secondary=classic.requirement,
    ):
        return

    intent = build_session_intent(
        primary=endurance.requirement,
        secondary=(
            classic.requirement,
        ),
    )

    intents.append(
        intent
    )

    _mark_represented(
        intent=intent,
        represented=represented,
    )

    _consume_one_occurrence(
        remaining=remaining,
        demand=endurance,
    )

    _consume_one_occurrence(
        remaining=remaining,
        demand=classic,
    )


def _build_long_endurance_intents(
    *,
    remaining: list[
        StimulusDemand
    ],
    intents: list[
        SessionIntent
    ],
    represented: list[
        TrainingStimulus
    ],
) -> None:
    long_endurance = _find_demand(
        remaining,
        TrainingStimulus.LONG_ENDURANCE,
    )

    if long_endurance is None:
        return

    for _ in range(
        long_endurance.target_occurrences
    ):
        secondary = tuple(
            demand.requirement
            for demand in remaining
            if (
                demand is not long_endurance
                and demand.target_occurrences > 0
                and demand.stimulus
                in _TRAIL_LONG_SESSION_SECONDARY_STIMULI
                and _can_share_session(
                    primary=long_endurance.requirement,
                    secondary=demand.requirement,
                )
            )
        )

        intent = build_session_intent(
            primary=long_endurance.requirement,
            secondary=secondary,
        )

        intent = replace(
            intent,
            duration_min_minutes=(
                long_endurance.requirement.duration_min_minutes
            ),
            duration_max_minutes=(
                long_endurance.requirement.duration_max_minutes
            ),
        )

        intents.append(
            intent
        )

        _mark_represented(
            intent=intent,
            represented=represented,
        )

    _consume_demand(
        remaining=remaining,
        demand=long_endurance,
    )

    for stimulus in (
        _TRAIL_LONG_SESSION_SECONDARY_STIMULI
    ):
        demand = _find_demand(
            remaining,
            stimulus,
        )

        if (
            demand is not None
            and stimulus in represented
        ):
            _consume_one_occurrence(
                remaining=remaining,
                demand=demand,
            )


def _build_separate_key_intents(
    *,
    remaining: list[
        StimulusDemand
    ],
    intents: list[
        SessionIntent
    ],
    represented: list[
        TrainingStimulus
    ],
) -> None:
    key_demands = tuple(
        demand
        for demand in remaining
        if (
            demand.requirement.priority
            is StimulusPriority.KEY
            and demand.target_occurrences > 0
        )
    )

    for demand in key_demands:
        for _ in range(
            demand.target_occurrences
        ):
            intent = build_session_intent(
                primary=demand.requirement,
            )

            intents.append(
                intent
            )

            _mark_represented(
                intent=intent,
                represented=represented,
            )

        _consume_demand(
            remaining=remaining,
            demand=demand,
        )


def _build_strength_intents(
    *,
    remaining: list[
        StimulusDemand
    ],
    intents: list[
        SessionIntent
    ],
    represented: list[
        TrainingStimulus
    ],
) -> None:
    lower_body = _find_demand(
        remaining,
        TrainingStimulus.STRENGTH_LOWER_BODY,
    )

    core = _find_demand(
        remaining,
        TrainingStimulus.STRENGTH_CORE,
    )

    if (
        lower_body is None
        and core is None
    ):
        return

    if (
        lower_body is not None
        and core is not None
        and lower_body.target_occurrences > 0
        and core.target_occurrences > 0
        and _can_share_session(
            primary=lower_body.requirement,
            secondary=core.requirement,
        )
    ):
        shared_occurrences = min(
            lower_body.target_occurrences,
            core.target_occurrences,
        )

        for _ in range(
            shared_occurrences
        ):
            intent = build_session_intent(
                primary=lower_body.requirement,
                secondary=(
                    core.requirement,
                ),
            )

            intents.append(
                intent
            )

            _mark_represented(
                intent=intent,
                represented=represented,
            )

        _consume_occurrences(
            remaining=remaining,
            demand=lower_body,
            occurrences=shared_occurrences,
        )

        _consume_occurrences(
            remaining=remaining,
            demand=core,
            occurrences=shared_occurrences,
        )

    for stimulus in (
        TrainingStimulus.STRENGTH_LOWER_BODY,
        TrainingStimulus.STRENGTH_CORE,
    ):
        demand = _find_demand(
            remaining,
            stimulus,
        )

        if demand is None:
            continue

        for _ in range(
            demand.target_occurrences
        ):
            intent = build_session_intent(
                primary=demand.requirement,
            )

            intents.append(
                intent
            )

            _mark_represented(
                intent=intent,
                represented=represented,
            )

        _consume_demand(
            remaining=remaining,
            demand=demand,
        )


def _build_remaining_intents(
    *,
    remaining: list[
        StimulusDemand
    ],
    intents: list[
        SessionIntent
    ],
    represented: list[
        TrainingStimulus
    ],
) -> None:
    ordered = tuple(
        sorted(
            remaining,
            key=_demand_sort_key,
        )
    )

    for demand in ordered:
        for occurrence_index in range(
            demand.target_occurrences
        ):
            intent = build_session_intent(
                primary=demand.requirement,
            )

            intent = replace(
                intent,
                required=(
                    occurrence_index
                    < demand.minimum_occurrences
                ),
            )

            intents.append(
                intent
            )

            _mark_represented(
                intent=intent,
                represented=represented,
            )

        _consume_demand(
            remaining=remaining,
            demand=demand,
        )


def _find_demand(
    demands: list[
        StimulusDemand
    ],
    stimulus: TrainingStimulus,
) -> StimulusDemand | None:
    for demand in demands:
        if demand.stimulus is stimulus:
            return demand

    return None


def _can_share_session(
    *,
    primary: TrainingStimulusRequirement,
    secondary: TrainingStimulusRequirement,
) -> bool:
    """Teste une compatibilité minimale avant fusion.

    build_session_intent reste l'autorité finale et validera
    également les modalités et durées consolidées.
    """

    primary_required = set(
        primary.required_modalities
    )

    secondary_required = set(
        secondary.required_modalities
    )

    if (
        primary_required
        and secondary_required
        and not (
            primary_required
            & secondary_required
        )
    ):
        return False

    if _is_strength_requirement(
        primary
    ) != _is_strength_requirement(
        secondary
    ):
        return False

    return _durations_can_overlap(
        primary=primary,
        secondary=secondary,
    )


def _durations_can_overlap(
    *,
    primary: TrainingStimulusRequirement,
    secondary: TrainingStimulusRequirement,
) -> bool:
    minimums = tuple(
        value
        for value in (
            primary.duration_min_minutes,
            secondary.duration_min_minutes,
        )
        if value is not None
    )

    maximums = tuple(
        value
        for value in (
            primary.duration_max_minutes,
            secondary.duration_max_minutes,
        )
        if value is not None
    )

    if not minimums or not maximums:
        return True

    return max(minimums) <= min(
        maximums
    )


def _is_strength_requirement(
    requirement: TrainingStimulusRequirement,
) -> bool:
    if requirement.stimulus in {
        TrainingStimulus.STRENGTH_LOWER_BODY,
        TrainingStimulus.STRENGTH_CORE,
    }:
        return True

    return (
        TrainingModality.STRENGTH
        in requirement.required_modalities
        or TrainingModality.STRENGTH
        in requirement.preferred_modalities
    )


def _demand_sort_key(
    demand: StimulusDemand,
) -> tuple[
    int,
    str,
]:
    priority = {
        StimulusPriority.KEY: 0,
        StimulusPriority.IMPORTANT: 1,
        StimulusPriority.SUPPORT: 2,
    }

    return (
        priority[
            demand.requirement.priority
        ],
        demand.stimulus.value,
    )


def _consume_demand(
    *,
    remaining: list[
        StimulusDemand
    ],
    demand: StimulusDemand,
) -> None:
    if demand in remaining:
        remaining.remove(
            demand
        )


def _consume_one_occurrence(
    *,
    remaining: list[
        StimulusDemand
    ],
    demand: StimulusDemand,
) -> None:
    _consume_occurrences(
        remaining=remaining,
        demand=demand,
        occurrences=1,
    )


def _consume_occurrences(
    *,
    remaining: list[
        StimulusDemand
    ],
    demand: StimulusDemand,
    occurrences: int,
) -> None:
    if occurrences <= 0:
        return

    new_target = max(
        0,
        demand.target_occurrences
        - occurrences,
    )

    if new_target == 0:
        _consume_demand(
            remaining=remaining,
            demand=demand,
        )

        return

    replacement = StimulusDemand(
        requirement=demand.requirement,
        minimum_occurrences=min(
            demand.minimum_occurrences,
            new_target,
        ),
        target_occurrences=new_target,
        maximum_occurrences=max(
            new_target,
            demand.maximum_occurrences
            - occurrences,
        ),
    )

    index = remaining.index(
        demand
    )

    remaining[
        index
    ] = replacement


def _mark_represented(
    *,
    intent: SessionIntent,
    represented: list[
        TrainingStimulus
    ],
) -> None:
    for stimulus in intent.stimuli:
        if stimulus not in represented:
            represented.append(
                stimulus
            )


def complete_session_intent_frequency(
    *,
    plan: SessionIntentPlan,
    target_session_count: int,
) -> SessionIntentPlan:
    """Complète prudemment la fréquence hebdomadaire.

    Les intentions métier déjà construites sont toujours conservées.

    Si la fréquence cible n'est pas atteinte, seules des intentions
    AEROBIC_EASY de soutien peuvent être ajoutées. Le moteur ne crée
    jamais artificiellement une exposition clé pour remplir un quota.

    Le nombre maximal d'occurrences autorisé par la demande
    hebdomadaire reste respecté.
    """

    if target_session_count < 0:
        raise ValueError(
            "La fréquence cible ne peut pas être négative."
        )

    if plan.session_count >= target_session_count:
        return plan

    aerobic_easy_demand = (
        plan.source_demand.demand_for(
            TrainingStimulus.AEROBIC_EASY
        )
    )

    if (
        aerobic_easy_demand is None
        or aerobic_easy_demand.maximum_occurrences <= 0
    ):
        return plan

    current_easy_occurrences = sum(
        1
        for intent in plan.intents
        if TrainingStimulus.AEROBIC_EASY
        in intent.stimuli
    )

    remaining_easy_capacity = max(
        0,
        aerobic_easy_demand.maximum_occurrences
        - current_easy_occurrences,
    )

    missing_sessions = (
        target_session_count
        - plan.session_count
    )

    additions = min(
        missing_sessions,
        remaining_easy_capacity,
    )

    if additions <= 0:
        return plan

    extra_intents = tuple(
        build_session_intent(
            primary=(
                aerobic_easy_demand.requirement
            ),
        )
        for _ in range(additions)
    )

    represented_stimuli = (
        plan.represented_stimuli
    )

    if (
        TrainingStimulus.AEROBIC_EASY
        not in represented_stimuli
    ):
        represented_stimuli = (
            *represented_stimuli,
            TrainingStimulus.AEROBIC_EASY,
        )

    unrepresented_stimuli = tuple(
        stimulus
        for stimulus in plan.unrepresented_stimuli
        if stimulus
        is not TrainingStimulus.AEROBIC_EASY
    )

    return SessionIntentPlan(
        intents=(
            *plan.intents,
            *extra_intents,
        ),
        source_demand=(
            plan.source_demand
        ),
        represented_stimuli=(
            represented_stimuli
        ),
        unrepresented_stimuli=(
            unrepresented_stimuli
        ),
    )
