"""Bridge entre le débrief hebdomadaire et le moteur de planning.

Ce module ne génère aucune séance.

Il traduit WeeklyAdaptationDecision vers les concepts déjà
compris par le moteur de trajectoire OpenCoach puis applique
uniquement les contraintes quantitatives qui ne possèdent pas
encore d'équivalent natif dans la trajectoire.

La charge n'est jamais multipliée directement ici :
LoadAdjustment reste l'autorité afin d'éviter une double
réduction.

Le volume, lui, peut être réduit par volume_factor car le moteur
de trajectoire ne possède pas encore ce facteur explicite.
"""

from __future__ import annotations

from dataclasses import replace

from opencoach.coaching.weekly_adaptation import (
    WeeklyAdaptationDecision,
    WeeklyIntensityPolicy,
    WeeklyLongRunPolicy,
    WeeklyStrengthPolicy,
)
from opencoach.planning.stimulus.training import (
    TrainingStimulus,
)
from opencoach.planning.trajectory.adjustment import (
    AdjustmentSeverity,
    TrajectoryAdjustment,
)
from opencoach.planning.trajectory.service import (
    CurrentWeekCoachingInput,
    CurrentWeekCoachingResult,
)


_HIGH_INTENSITY_STIMULI = (
    TrainingStimulus.SPEED_DEVELOPMENT,
    TrainingStimulus.VO2MAX,
)

_QUALITY_STIMULI = (
    TrainingStimulus.THRESHOLD,
    TrainingStimulus.SPEED_DEVELOPMENT,
    TrainingStimulus.VO2MAX,
    TrainingStimulus.UPHILL_STRENGTH,
    TrainingStimulus.UPHILL_STRENGTH_ENDURANCE,
    TrainingStimulus.UPHILL_THRESHOLD,
    TrainingStimulus.DOWNHILL_SPECIFICITY,
    TrainingStimulus.RACE_SPECIFIC,
)

_LOWER_BODY_STRENGTH_STIMULI = (
    TrainingStimulus.STRENGTH_LOWER_BODY,
)


def build_weekly_trajectory_adjustment(
    decision: WeeklyAdaptationDecision,
) -> TrajectoryAdjustment:
    """Convertit T6.3 vers le mécanisme natif de trajectoire."""

    if decision.allow_missed_volume_catchup:
        raise ValueError(
            "Le rattrapage automatique de volume "
            "est interdit."
        )

    suppressed = list(
        _suppressed_stimuli(decision)
    )

    return TrajectoryAdjustment(
        reason=decision.reason,
        severity=_severity(decision),
        load=decision.load_adjustment,
        progression=(
            decision.progression_adjustment
        ),
        suppressed_stimuli=tuple(suppressed),
        allow_schedule_compression=False,
        athlete_override_allowed=True,
        notes=tuple(decision.guardrails),
    )


def apply_weekly_adaptation_to_planning_input(
    *,
    planning_input: CurrentWeekCoachingInput,
    decision: WeeklyAdaptationDecision,
) -> CurrentWeekCoachingInput:
    """Injecte T6.3 dans les adaptations natives du planning."""

    adjustment = (
        build_weekly_trajectory_adjustment(
            decision
        )
    )

    return replace(
        planning_input,
        additional_adjustments=(
            planning_input.additional_adjustments
            + (adjustment,)
        ),
    )


def apply_weekly_adaptation_to_planning_result(
    *,
    planning: CurrentWeekCoachingResult,
    decision: WeeklyAdaptationDecision,
) -> CurrentWeekCoachingResult:
    """Applique le budget temporel T6.3 à l'enveloppe finale.

    La cible de charge n'est volontairement PAS remultipliée ici.
    Elle a déjà été adaptée par LoadAdjustment dans le moteur
    de trajectoire.
    """

    envelope = planning.coaching.envelope

    target_duration = (
        None
        if envelope.target_duration_minutes is None
        else envelope.target_duration_minutes
             if decision.volume_factor == 1.0
             else round(
            envelope.target_duration_minutes
            * decision.volume_factor,
            1,
        )
    )

    long_endurance_reference = (
        _adapt_long_endurance_reference(
            value=(
                envelope.long_endurance_reference_minutes
            ),
            decision=decision,
        )
    )

    notes = envelope.notes + (
        (
            "Adaptation hebdomadaire OpenCoach : "
            + decision.reason
        ),
    )

    trajectory_week = planning.coaching.trajectory_week

    capped_target_load = envelope.target_load

    if (
        trajectory_week is not None
        and envelope.target_load is not None
    ):
        capped_target_load = (
            _apply_maximum_progression_rate(
                target_load=envelope.target_load,
                progression_reference_before=(
                    trajectory_week.progression_reference_before
                ),
                maximum_progression_rate=(
                    decision.maximum_progression_rate
                ),
            )
        )

    adapted_envelope = replace(
        envelope,
        target_load=capped_target_load,
        target_duration_minutes=target_duration,
        long_endurance_reference_minutes=(
            long_endurance_reference
        ),
        notes=notes,
    )

    adapted_coaching = replace(
        planning.coaching,
        envelope=adapted_envelope,
    )

    return replace(
        planning,
        coaching=adapted_coaching,
    )

def _suppressed_stimuli(
    decision: WeeklyAdaptationDecision,
) -> tuple[TrainingStimulus, ...]:
    result: list[TrainingStimulus] = []

    if (
        decision.intensity_policy
        is WeeklyIntensityPolicy.REDUCE
    ):
        result.extend(
            _HIGH_INTENSITY_STIMULI
        )

    elif (
        decision.intensity_policy
        is WeeklyIntensityPolicy.RECOVERY_ONLY
    ):
        result.extend(
            _QUALITY_STIMULI
        )

    if (
        decision.long_run_policy
        is WeeklyLongRunPolicy.OPTIONAL
    ):
        result.append(
            TrainingStimulus.LONG_ENDURANCE
        )

    if (
        decision.strength_policy
        is WeeklyStrengthPolicy.REDUCE
    ):
        result.extend(
            _LOWER_BODY_STRENGTH_STIMULI
        )

    return tuple(dict.fromkeys(result))


def _adapt_long_endurance_reference(
    *,
    value: float | None,
    decision: WeeklyAdaptationDecision,
) -> float | None:
    if value is None:
        return None

    if (
        decision.long_run_policy
        is WeeklyLongRunPolicy.REDUCE
    ):
        return round(
            value * decision.volume_factor,
            1,
        )

    if (
        decision.long_run_policy
        is WeeklyLongRunPolicy.OPTIONAL
    ):
        return round(
            value * decision.volume_factor,
            1,
        )

    return value


def _severity(
    decision: WeeklyAdaptationDecision,
) -> AdjustmentSeverity:
    if decision.load_factor <= 0.75:
        return AdjustmentSeverity.MAJOR

    if decision.load_factor < 1.0:
        return AdjustmentSeverity.MODERATE

    return AdjustmentSeverity.MINOR



def _apply_maximum_progression_rate(
    *,
    target_load: float,
    progression_reference_before: float,
    maximum_progression_rate: float,
) -> float:
    """Plafonne la progression décidée par T6.3.

    La référence utilisée est la référence de progression de la
    trajectoire avant application de la politique de la semaine.

    Ce garde-fou :
    - ne recalcule jamais la trajectoire ;
    - n'applique aucun facteur de charge ;
    - ne crée jamais de progression ;
    - ne peut que limiter une cible déjà produite par le moteur.
    """

    if target_load < 0:
        raise ValueError(
            "La charge cible ne peut pas être négative."
        )

    if progression_reference_before < 0:
        raise ValueError(
            "La référence de progression "
            "ne peut pas être négative."
        )

    if not (
        0.0
        <= maximum_progression_rate
        <= 0.10
    ):
        raise ValueError(
            "Le plafond de progression doit être "
            "compris entre 0 et 10 %."
        )

    maximum_allowed_load = (
        progression_reference_before
        * (
            1.0
            + maximum_progression_rate
        )
    )

    return min(
        target_load,
        maximum_allowed_load,
    )
