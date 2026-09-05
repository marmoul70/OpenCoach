"""Décision d'adaptation hebdomadaire OpenCoach.

Ce module traduit un WeeklyDebrief en directive d'adaptation pour
le moteur de planning.

Il ne crée, ne déplace et ne modifie aucune séance.

Principe architectural :

    Le débrief décide de la direction d'adaptation.
    Le moteur de planning reste responsable de fabriquer
    une semaine cohérente.

Les facteurs de charge et de volume sont exclusivement des facteurs
de réduction. Une valeur de 1.0 signifie que le moteur de planning
conserve sa progression normale par phase.

Ce module n'ajoute donc jamais lui-même une progression positive
au volume ou à la charge.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from opencoach.coaching.weekly_debrief import (
    WeeklyAdaptationDirection,
    WeeklyDebrief,
    WeeklyDebriefVerdict,
)
from opencoach.planning.trajectory.adjustment import (
    LoadAdjustment,
    ProgressionAdjustment,
)


class WeeklyIntensityPolicy(StrEnum):
    """Politique d'intensité transmise au moteur de planning."""

    MAINTAIN = "maintain"
    PROTECT_KEY = "protect_key"
    REDUCE = "reduce"
    RECOVERY_ONLY = "recovery_only"


class WeeklyLongRunPolicy(StrEnum):
    """Politique concernant la sortie longue."""

    MAINTAIN = "maintain"
    PROTECT = "protect"
    REDUCE = "reduce"
    OPTIONAL = "optional"


class WeeklyStrengthPolicy(StrEnum):
    """Politique concernant le renforcement."""

    MAINTAIN = "maintain"
    REDUCE = "reduce"
    OPTIONAL = "optional"


@dataclass(frozen=True, slots=True)
class WeeklyAdaptationDecision:
    """Directive structurée pour la semaine suivante.

    Les facteurs ne doivent jamais être supérieurs à 1.0.

    Une progression positive reste entièrement sous la
    responsabilité du moteur de trajectoire hebdomadaire.
    """

    direction: WeeklyAdaptationDirection

    load_adjustment: LoadAdjustment
    progression_adjustment: ProgressionAdjustment

    load_factor: float
    volume_factor: float

    maximum_progression_rate: float

    intensity_policy: WeeklyIntensityPolicy
    long_run_policy: WeeklyLongRunPolicy
    strength_policy: WeeklyStrengthPolicy

    allow_missed_volume_catchup: bool

    reason: str
    guardrails: tuple[str, ...]

    def __post_init__(self) -> None:
        for name, value in (
            ("load_factor", self.load_factor),
            ("volume_factor", self.volume_factor),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(
                    f"{name} doit être compris entre 0 et 1."
                )

        if not (
            0.0
            <= self.maximum_progression_rate
            <= 0.10
        ):
            raise ValueError(
                "maximum_progression_rate doit être "
                "compris entre 0 et 0.10."
            )

        if self.allow_missed_volume_catchup:
            raise ValueError(
                "OpenCoach ne doit jamais rattraper "
                "automatiquement le volume manqué."
            )

        if not self.reason.strip():
            raise ValueError(
                "La raison d'adaptation ne peut pas être vide."
            )

        if not self.guardrails:
            raise ValueError(
                "Une décision hebdomadaire doit comporter "
                "au moins un garde-fou."
            )


COMMON_GUARDRAILS = (
    "Ne pas rattraper automatiquement la charge ou le volume manqué.",
    "Ne pas ajouter plusieurs séances difficiles pour compenser.",
    "Respecter la phase de préparation, l'affûtage et la récupération.",
    "Le moteur de planning conserve la responsabilité des séances.",
)


def build_weekly_adaptation_decision(
    debrief: WeeklyDebrief,
) -> WeeklyAdaptationDecision:
    """Construit la directive de la semaine suivante.

    La décision est déterministe et sans effet de bord.

    Le verdict constitue le signal principal. La direction T6.1
    est vérifiée afin de détecter une incohérence de domaine.
    """

    expected_direction = _expected_direction(
        debrief.verdict
    )

    if debrief.adaptation_direction is not expected_direction:
        raise ValueError(
            "Le verdict et la direction du WeeklyDebrief "
            "sont incohérents."
        )

    if debrief.verdict is WeeklyDebriefVerdict.UNKNOWN:
        return _decision(
            direction=WeeklyAdaptationDirection.OBSERVE,
            load_adjustment=LoadAdjustment.MAINTAIN,
            progression_adjustment=ProgressionAdjustment.PAUSE,
            load_factor=1.0,
            volume_factor=1.0,
            maximum_progression_rate=0.0,
            intensity_policy=WeeklyIntensityPolicy.MAINTAIN,
            long_run_policy=WeeklyLongRunPolicy.MAINTAIN,
            strength_policy=WeeklyStrengthPolicy.MAINTAIN,
            reason=(
                "Données hebdomadaires insuffisantes : "
                "la progression est gelée jusqu'à disposer "
                "d'un bilan exploitable."
            ),
        )

    if (
        debrief.verdict
        is WeeklyDebriefVerdict.VERY_PRODUCTIVE
    ):
        return _decision(
            direction=WeeklyAdaptationDirection.PROGRESS,
            load_adjustment=LoadAdjustment.MAINTAIN,
            progression_adjustment=ProgressionAdjustment.CONTINUE,
            load_factor=1.0,
            volume_factor=1.0,
            maximum_progression_rate=0.10,
            intensity_policy=WeeklyIntensityPolicy.PROTECT_KEY,
            long_run_policy=WeeklyLongRunPolicy.PROTECT,
            strength_policy=WeeklyStrengthPolicy.MAINTAIN,
            reason=(
                "Semaine très productive : la progression "
                "normale du moteur peut continuer sans "
                "majoration supplémentaire."
            ),
        )

    if debrief.verdict in {
        WeeklyDebriefVerdict.PRODUCTIVE,
        WeeklyDebriefVerdict.CORRECT,
    }:
        return _decision(
            direction=WeeklyAdaptationDirection.MAINTAIN,
            load_adjustment=LoadAdjustment.MAINTAIN,
            progression_adjustment=ProgressionAdjustment.CONTINUE,
            load_factor=1.0,
            volume_factor=1.0,
            maximum_progression_rate=0.10,
            intensity_policy=WeeklyIntensityPolicy.MAINTAIN,
            long_run_policy=WeeklyLongRunPolicy.MAINTAIN,
            strength_policy=WeeklyStrengthPolicy.MAINTAIN,
            reason=(
                "Semaine suffisamment conforme : le moteur "
                "peut conserver la trajectoire prévue."
            ),
        )

    if (
        debrief.verdict
        is WeeklyDebriefVerdict.PARTIALLY_COMPLIANT
    ):
        return _decision(
            direction=WeeklyAdaptationDirection.REDUCE,
            load_adjustment=LoadAdjustment.REDUCE_SLIGHTLY,
            progression_adjustment=ProgressionAdjustment.SLOW,
            load_factor=0.90,
            volume_factor=0.90,
            maximum_progression_rate=0.0,
            intensity_policy=WeeklyIntensityPolicy.REDUCE,
            long_run_policy=WeeklyLongRunPolicy.REDUCE,
            strength_policy=WeeklyStrengthPolicy.MAINTAIN,
            reason=(
                "Semaine partiellement conforme : réduire "
                "légèrement la demande et ne pas compenser "
                "les séances manquées."
            ),
        )

    if (
        debrief.verdict
        is WeeklyDebriefVerdict.INSUFFICIENT
    ):
        return _decision(
            direction=WeeklyAdaptationDirection.RECOVER,
            load_adjustment=LoadAdjustment.REDUCE,
            progression_adjustment=ProgressionAdjustment.PAUSE,
            load_factor=0.80,
            volume_factor=0.80,
            maximum_progression_rate=0.0,
            intensity_policy=WeeklyIntensityPolicy.REDUCE,
            long_run_policy=WeeklyLongRunPolicy.OPTIONAL,
            strength_policy=WeeklyStrengthPolicy.REDUCE,
            reason=(
                "Semaine insuffisamment réalisée : revenir "
                "à une charge assimilable avant toute nouvelle "
                "progression."
            ),
        )

    if debrief.verdict is WeeklyDebriefVerdict.OVERLOAD:
        return _decision(
            direction=WeeklyAdaptationDirection.RECOVER,
            load_adjustment=LoadAdjustment.REDUCE,
            progression_adjustment=ProgressionAdjustment.PAUSE,
            load_factor=0.75,
            volume_factor=0.75,
            maximum_progression_rate=0.0,
            intensity_policy=WeeklyIntensityPolicy.RECOVERY_ONLY,
            long_run_policy=WeeklyLongRunPolicy.OPTIONAL,
            strength_policy=WeeklyStrengthPolicy.REDUCE,
            reason=(
                "Surcharge hebdomadaire détectée : priorité "
                "à l'assimilation et à la récupération avant "
                "la reprise de la progression."
            ),
        )

    raise ValueError(
        f"Verdict hebdomadaire non pris en charge : "
        f"{debrief.verdict!r}"
    )


def _decision(
    *,
    direction: WeeklyAdaptationDirection,
    load_adjustment: LoadAdjustment,
    progression_adjustment: ProgressionAdjustment,
    load_factor: float,
    volume_factor: float,
    maximum_progression_rate: float,
    intensity_policy: WeeklyIntensityPolicy,
    long_run_policy: WeeklyLongRunPolicy,
    strength_policy: WeeklyStrengthPolicy,
    reason: str,
) -> WeeklyAdaptationDecision:
    return WeeklyAdaptationDecision(
        direction=direction,
        load_adjustment=load_adjustment,
        progression_adjustment=progression_adjustment,
        load_factor=load_factor,
        volume_factor=volume_factor,
        maximum_progression_rate=maximum_progression_rate,
        intensity_policy=intensity_policy,
        long_run_policy=long_run_policy,
        strength_policy=strength_policy,
        allow_missed_volume_catchup=False,
        reason=reason,
        guardrails=COMMON_GUARDRAILS,
    )


def _expected_direction(
    verdict: WeeklyDebriefVerdict,
) -> WeeklyAdaptationDirection:
    mapping = {
        WeeklyDebriefVerdict.UNKNOWN:
            WeeklyAdaptationDirection.OBSERVE,
        WeeklyDebriefVerdict.VERY_PRODUCTIVE:
            WeeklyAdaptationDirection.PROGRESS,
        WeeklyDebriefVerdict.PRODUCTIVE:
            WeeklyAdaptationDirection.MAINTAIN,
        WeeklyDebriefVerdict.CORRECT:
            WeeklyAdaptationDirection.MAINTAIN,
        WeeklyDebriefVerdict.PARTIALLY_COMPLIANT:
            WeeklyAdaptationDirection.REDUCE,
        WeeklyDebriefVerdict.INSUFFICIENT:
            WeeklyAdaptationDirection.RECOVER,
        WeeklyDebriefVerdict.OVERLOAD:
            WeeklyAdaptationDirection.RECOVER,
    }

    return mapping[verdict]
