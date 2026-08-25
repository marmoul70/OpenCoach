"""Allocation déterministe des durées hebdomadaires.

Ce module répartit un budget de durée relatif entre les intentions
déjà planifiées.

Il ne choisit :
- ni les jours ;
- ni les stimuli ;
- ni les modalités ;
- ni le contenu concret des séances.

La charge cible influence le volume global de manière relative.
Elle ne représente pas une conversion physiologique directe
entre points de charge et minutes.
"""

from __future__ import annotations

from opencoach.planning.sessions.intent import (
    SessionIntentImportance,
)
from opencoach.planning.stimulus.training import (
    TrainingStimulus,
)
from opencoach.planning.sessions.families import (
    session_intent_family,
)
from opencoach.planning.stimulus.families import (
    StimulusFamily,
)
from opencoach.planning.weekly.session_intent_slot import (
    WeeklySessionIntentSlot,
)

from .models import (
    AllocatedSessionDuration,
)


_IMPORTANCE_WEIGHT = {
    SessionIntentImportance.SUPPORT: 1.0,
    SessionIntentImportance.IMPORTANT: 1.25,
    SessionIntentImportance.KEY: 1.5,
}


_STIMULUS_WEIGHT = {
    TrainingStimulus.LONG_ENDURANCE: 1.35,
    TrainingStimulus.RACE_SPECIFIC: 1.20,
}


def allocate_session_durations(
    *,
    slots: tuple[
        WeeklySessionIntentSlot,
        ...,
    ],
    target_load: float,
    reference_weekly_duration_minutes: float | None = None,
    long_endurance_reference_minutes: float | None = None,
) -> tuple[
    AllocatedSessionDuration,
    ...,
]:
    """Alloue une durée compatible à chaque créneau."""

    if target_load < 0:
        raise ValueError(
            "La charge cible ne peut pas être négative."
        )

    if not slots:
        return ()

    if target_load == 0:
        return tuple(
            AllocatedSessionDuration(
                slot_id=slot.slot_id,
                duration_minutes=(
                    _minimum_duration(
                        slot
                    )
                ),
            )
            for slot in slots
        )
    
    if (
        reference_weekly_duration_minutes
        is not None
        and reference_weekly_duration_minutes <= 0
    ):
        raise ValueError(
            "La durée hebdomadaire de référence "
            "doit être strictement positive."
        )

    if (
        long_endurance_reference_minutes
        is not None
        and long_endurance_reference_minutes <= 0
    ):
        raise ValueError(
            "La durée de référence de sortie longue "
            "doit être strictement positive."
        )

    target_weekly_minutes = (
        _target_weekly_minutes(
            target_load=target_load,
            session_count=len(slots),
            reference_weekly_duration_minutes=(
                reference_weekly_duration_minutes
            ),
        )
    )

    if (
        long_endurance_reference_minutes
        is not None
    ):
        return _allocate_with_long_endurance_reference(
            slots=slots,
            target_weekly_minutes=(
                target_weekly_minutes
            ),
            long_endurance_reference_minutes=(
                long_endurance_reference_minutes
            ),
        )

    weights = tuple(
        _slot_weight(
            slot
        )
        for slot in slots
    )

    total_weight = sum(
        weights
    )

    result = tuple(
        AllocatedSessionDuration(
            slot_id=slot.slot_id,
            duration_minutes=(
                _resolve_slot_duration(
                    slot=slot,
                    target_minutes=(
                        target_weekly_minutes
                        * weight
                        / total_weight
                    ),
                )
            ),
        )
        for slot, weight
        in zip(
            slots,
            weights,
            strict=True,
        )
    )

    durations = {
        item.slot_id: item.duration_minutes
        for item in result
    }

    durations = _reconcile_allocated_budget(
        slots=slots,
        durations=durations,
        target_weekly_minutes=(
            target_weekly_minutes
        ),
    )

    return tuple(
        AllocatedSessionDuration(
            slot_id=slot.slot_id,
            duration_minutes=(
                durations[
                    slot.slot_id
                ]
            ),
        )
        for slot in slots
    )


def _allocate_with_long_endurance_reference(
    *,
    slots: tuple[
        WeeklySessionIntentSlot,
        ...,
    ],
    target_weekly_minutes: float,
    long_endurance_reference_minutes: float,
) -> tuple[
    AllocatedSessionDuration,
    ...
]:
    """Réserve la sortie longue avant de répartir le reliquat."""

    long_slots = tuple(
        slot
        for slot in slots
        if (
            slot.intent.primary_stimulus
            is TrainingStimulus.LONG_ENDURANCE
        )
    )

    if len(long_slots) != 1:
        weights = tuple(
            _slot_weight(slot)
            for slot in slots
        )

        total_weight = sum(weights)

        initial_allocations = tuple(
            AllocatedSessionDuration(
                slot_id=slot.slot_id,
                duration_minutes=(
                    _resolve_slot_duration(
                        slot=slot,
                        target_minutes=(
                            target_weekly_minutes
                            * weight
                            / total_weight
                        ),
                    )
                ),
            )
            for slot, weight
            in zip(
                slots,
                weights,
                strict=True,
            )
        )

        durations = {
            item.slot_id: item.duration_minutes
            for item in initial_allocations
        }

        durations = _reconcile_allocated_budget(
            slots=slots,
            durations=durations,
            target_weekly_minutes=(
                target_weekly_minutes
            ),
        )

        return tuple(
            AllocatedSessionDuration(
                slot_id=slot.slot_id,
                duration_minutes=(
                    durations[
                        slot.slot_id
                    ]
                ),
            )
            for slot in slots
        )

    long_slot = long_slots[0]

    other_slots = tuple(
        slot
        for slot in slots
        if slot is not long_slot
    )

    other_minimum_total = sum(
        _minimum_duration(slot)
        for slot in other_slots
    )

    long_maximum = _maximum_duration(
        long_slot
    )

    long_budget_ceiling = max(
        _minimum_duration(long_slot),
        int(
            target_weekly_minutes
            - other_minimum_total
        ),
    )

    long_target = min(
        long_endurance_reference_minutes,
        float(long_budget_ceiling),
    )

    if long_maximum is not None:
        long_target = min(
            long_target,
            float(long_maximum),
        )

    long_duration = _resolve_slot_duration(
        slot=long_slot,
        target_minutes=long_target,
    )

    remaining_budget = max(
        0.0,
        target_weekly_minutes
        - long_duration,
    )

    if not other_slots:
        return (
            AllocatedSessionDuration(
                slot_id=long_slot.slot_id,
                duration_minutes=long_duration,
            ),
        )

    other_allocations = [
        AllocatedSessionDuration(
            slot_id=slot.slot_id,
            duration_minutes=(
                _functional_minimum_duration(
                    slot
                )
            ),
        )
        for slot in other_slots
    ]

    durations = {
        item.slot_id: item.duration_minutes
        for item in other_allocations
    }

    durations[
        long_slot.slot_id
    ] = long_duration

    durations = _reconcile_allocated_budget(
        slots=slots,
        durations=durations,
        target_weekly_minutes=(
            target_weekly_minutes
        ),
        protected_slot_ids=frozenset(
            {
                long_slot.slot_id,
            }
        ),
    )

    return tuple(
        AllocatedSessionDuration(
            slot_id=slot.slot_id,
            duration_minutes=(
                durations[
                    slot.slot_id
                ]
            ),
        )
        for slot in slots
    )


_FUNCTIONAL_MINIMUM_BY_FAMILY = {
    StimulusFamily.THRESHOLD: 60,
    StimulusFamily.HIGH_INTENSITY: 60,
    StimulusFamily.SPECIFIC: 60,
}


def _functional_minimum_duration(
    slot: WeeklySessionIntentSlot,
) -> int:
    """Retourne la durée minimale fonctionnelle d'une séance.

    Le minimum de l'intention reste la borne absolue.

    Certaines familles qualitatives nécessitent néanmoins une durée
    totale suffisante pour contenir échauffement, travail principal
    et retour au calme sans être artificiellement comprimées.
    """

    minimum = _minimum_duration(
        slot
    )

    family = session_intent_family(
        slot.intent
    )

    functional_minimum = max(
        minimum,
        _FUNCTIONAL_MINIMUM_BY_FAMILY.get(
            family,
            minimum,
        ),
    )

    maximum = _maximum_duration(
        slot
    )

    if maximum is not None:
        functional_minimum = min(
            functional_minimum,
            maximum,
        )

    return functional_minimum


_VOLUME_ABSORPTION_PRIORITY = {
    StimulusFamily.AEROBIC: 0,
    StimulusFamily.SPECIFIC: 1,
    StimulusFamily.THRESHOLD: 2,
    StimulusFamily.HIGH_INTENSITY: 3,
    StimulusFamily.RECOVERY: 4,
    StimulusFamily.STRENGTH: 5,
}


def _volume_absorption_rank(
    slot: WeeklySessionIntentSlot,
) -> tuple[
    int,
    float,
]:
    """Classe les créneaux selon leur capacité à absorber du volume facile.

    Les familles aérobies absorbent le surplus avant les familles
    qualitatives. L'importance départage ensuite les séances appartenant
    à une même famille.
    """

    family = session_intent_family(
        slot.intent
    )

    return (
        _VOLUME_ABSORPTION_PRIORITY[
            family
        ],
        -_slot_weight(slot),
    )


def _reconcile_allocated_budget(
    *,
    slots: tuple[
        WeeklySessionIntentSlot,
        ...,
    ],
    durations: dict[str, int],
    target_weekly_minutes: float,
    protected_slot_ids: frozenset[str] = frozenset(),
) -> dict[str, int]:
    """Réconcilie les arrondis avec le budget hebdomadaire cible."""

    target = _round_to_five(
        target_weekly_minutes
    )

    current = sum(
        durations.values()
    )

    difference = target - current

    if difference == 0:
        return durations

    if difference < 0:
        remaining = -difference

        candidates = sorted(
            (
                slot
                for slot in slots
                if slot.slot_id
                not in protected_slot_ids
            ),
            key=lambda slot: (
                durations[slot.slot_id]
                - _minimum_duration(slot)
            ),
            reverse=True,
        )

        for slot in candidates:
            while (
                remaining >= 5
                and durations[slot.slot_id] - 5
                >= _minimum_duration(slot)
            ):
                durations[slot.slot_id] -= 5
                remaining -= 5

                if remaining == 0:
                    return durations

    else:
        remaining = difference

        candidates = tuple(
            sorted(
                (
                    slot
                    for slot in slots
                    if slot.slot_id
                    not in protected_slot_ids
                ),
                key=_volume_absorption_rank,
            )
        )

        priorities = tuple(
            sorted(
                {
                    _volume_absorption_rank(
                        slot
                    )[0]
                    for slot in candidates
                }
            )
        )

        for priority in priorities:
            family_candidates = tuple(
                slot
                for slot in candidates
                if (
                    _volume_absorption_rank(
                        slot
                    )[0]
                    == priority
                )
            )

            while remaining >= 5:
                progressed = False

                for slot in family_candidates:
                    maximum = _maximum_duration(
                        slot
                    )

                    if (
                        maximum is not None
                        and durations[
                            slot.slot_id
                        ] + 5
                        > maximum
                    ):
                        continue

                    durations[
                        slot.slot_id
                    ] += 5

                    remaining -= 5
                    progressed = True

                    if remaining < 5:
                        return durations

                if not progressed:
                    break

    return durations


def _target_weekly_minutes(
    *,
    target_load: float,
    session_count: int,
    reference_weekly_duration_minutes: float | None,
) -> float:
    """Construit le budget de durée hebdomadaire.

    La durée historique constitue la référence prioritaire.

    Le fallback fondé sur le nombre de séances reste temporairement
    disponible tant que toutes les couches du pipeline ne transmettent
    pas encore la baseline temporelle.
    """

    if reference_weekly_duration_minutes is not None:
        return reference_weekly_duration_minutes

    baseline = (
        session_count
        * 45.0
    )

    load_component = (
        target_load
        * 0.60
    )

    return max(
        baseline,
        load_component,
    )

def _slot_weight(
    slot: WeeklySessionIntentSlot,
) -> float:
    intent = slot.intent

    weight = (
        _IMPORTANCE_WEIGHT[
            intent.importance
        ]
    )

    weight *= (
        _STIMULUS_WEIGHT.get(
            intent.primary_stimulus,
            1.0,
        )
    )

    return weight


def _resolve_slot_duration(
    *,
    slot: WeeklySessionIntentSlot,
    target_minutes: float,
) -> int:
    minimum = (
        _minimum_duration(
            slot
        )
    )

    maximum = (
        _maximum_duration(
            slot
        )
    )

    duration = (
        _round_to_five(
            target_minutes
        )
    )

    duration = max(
        duration,
        minimum,
    )

    if maximum is not None:
        duration = min(
            duration,
            maximum,
        )

    return duration


def _minimum_duration(
    slot: WeeklySessionIntentSlot,
) -> int:
    return (
        slot.intent.duration_min_minutes
        if slot.intent.duration_min_minutes
        is not None
        else 15
    )


def _maximum_duration(
    slot: WeeklySessionIntentSlot,
) -> int | None:
    candidates: list[int] = []

    if (
        slot.intent.duration_max_minutes
        is not None
    ):
        candidates.append(
            slot.intent.duration_max_minutes
        )

    if (
        slot.duration_available_minutes
        is not None
    ):
        candidates.append(
            slot.duration_available_minutes
        )

    if not candidates:
        return None

    return min(
        candidates
    )


def _round_to_five(
    value: float,
) -> int:
    return max(
        5,
        int(
            round(
                value / 5
            )
            * 5
        ),
    )
