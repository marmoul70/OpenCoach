"""Domaine pur du débrief hebdomadaire OpenCoach.

Ce module transforme les faits consolidés d'une semaine terminée en un
bilan objectif. Il ne lit ni SQLAlchemy, ni FastAPI, ni les repositories.

La collecte des données et l'adaptation effective du planning appartiennent
aux couches applicatives suivantes de T6.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum


class WeeklyDebriefVerdict(StrEnum):
    """Verdict synthétique d'une semaine d'entraînement terminée."""

    VERY_PRODUCTIVE = "very_productive"
    PRODUCTIVE = "productive"
    CORRECT = "correct"
    PARTIALLY_COMPLIANT = "partially_compliant"
    INSUFFICIENT = "insufficient"
    OVERLOAD = "overload"
    UNKNOWN = "unknown"


class WeeklyAdaptationDirection(StrEnum):
    """Direction proposée au moteur de planning pour la semaine suivante."""

    PROGRESS = "progress"
    MAINTAIN = "maintain"
    REDUCE = "reduce"
    RECOVER = "recover"
    OBSERVE = "observe"


@dataclass(frozen=True, slots=True)
class WeeklyDebriefFacts:
    """Faits consolidés pour une semaine civile terminée."""

    week_start: date
    week_end: date

    planned_sessions: int
    completed_sessions: int
    skipped_sessions: int
    supplementary_sessions: int = 0

    planned_duration_minutes: int = 0
    actual_duration_minutes: int = 0

    planned_load: float = 0.0
    actual_load: float = 0.0

    key_sessions_planned: int = 0
    key_sessions_completed: int = 0

    compliant_intensity_sessions: int = 0
    analyzed_intensity_sessions: int = 0

    history_confidence: float = 1.0


@dataclass(frozen=True, slots=True)
class WeeklyDebrief:
    """Résultat déterministe du bilan hebdomadaire."""

    week_start: date
    week_end: date

    verdict: WeeklyDebriefVerdict
    adaptation_direction: WeeklyAdaptationDirection

    overall_score: int | None
    adherence_score: int | None
    duration_score: int | None
    load_score: int | None
    key_sessions_score: int | None
    intensity_score: int | None

    completion_ratio: float | None
    duration_ratio: float | None
    load_ratio: float | None

    headline: str
    analysis: str
    strengths: tuple[str, ...]
    warnings: tuple[str, ...]


def _validate_facts(facts: WeeklyDebriefFacts) -> None:
    if facts.week_end < facts.week_start:
        raise ValueError("week_end doit être postérieur ou égal à week_start.")

    integer_values = (
        facts.planned_sessions,
        facts.completed_sessions,
        facts.skipped_sessions,
        facts.supplementary_sessions,
        facts.planned_duration_minutes,
        facts.actual_duration_minutes,
        facts.key_sessions_planned,
        facts.key_sessions_completed,
        facts.compliant_intensity_sessions,
        facts.analyzed_intensity_sessions,
    )

    if any(value < 0 for value in integer_values):
        raise ValueError("Les compteurs du débrief ne peuvent pas être négatifs.")

    if facts.planned_load < 0 or facts.actual_load < 0:
        raise ValueError("Les charges du débrief ne peuvent pas être négatives.")

    if not 0.0 <= facts.history_confidence <= 1.0:
        raise ValueError("history_confidence doit être comprise entre 0 et 1.")

    if facts.completed_sessions > facts.planned_sessions:
        raise ValueError(
            "completed_sessions ne peut pas dépasser planned_sessions ; "
            "utilisez supplementary_sessions pour les séances supplémentaires."
        )

    if facts.skipped_sessions > facts.planned_sessions:
        raise ValueError("skipped_sessions ne peut pas dépasser planned_sessions.")

    if (
        facts.completed_sessions + facts.skipped_sessions
        > facts.planned_sessions
    ):
        raise ValueError(
            "Une séance planifiée ne peut pas être à la fois réalisée et ignorée."
        )

    if facts.key_sessions_completed > facts.key_sessions_planned:
        raise ValueError(
            "key_sessions_completed ne peut pas dépasser key_sessions_planned."
        )

    if (
        facts.compliant_intensity_sessions
        > facts.analyzed_intensity_sessions
    ):
        raise ValueError(
            "compliant_intensity_sessions ne peut pas dépasser "
            "analyzed_intensity_sessions."
        )


def _ratio(actual: float, planned: float) -> float | None:
    if planned <= 0:
        return None

    return actual / planned


def _bounded_score_from_ratio(ratio: float | None) -> int | None:
    """Score de proximité à la cible, borné à 0..100.

    La cible parfaite vaut 1.0. Un dépassement n'accorde jamais de bonus :
    au-delà de la cible, le score redescend symétriquement afin qu'une
    surcharge ne puisse pas être récompensée.
    """

    if ratio is None:
        return None

    deviation = abs(ratio - 1.0)
    return max(0, min(100, round(100 * (1.0 - deviation))))


def _percentage_score(
    completed: int,
    planned: int,
) -> int | None:
    if planned <= 0:
        return None

    return max(
        0,
        min(
            100,
            round(100 * completed / planned),
        ),
    )


def _weighted_score(
    values: tuple[tuple[int | None, float], ...],
) -> int | None:
    usable = [
        (score, weight)
        for score, weight in values
        if score is not None
    ]

    if not usable:
        return None

    weighted_sum = sum(
        score * weight
        for score, weight in usable
    )
    total_weight = sum(weight for _, weight in usable)

    return max(
        0,
        min(
            100,
            round(weighted_sum / total_weight),
        ),
    )


def _format_ratio(ratio: float | None) -> str:
    if ratio is None:
        return "non mesurable"

    return f"{ratio * 100:.0f} %"


def build_weekly_debrief(
    facts: WeeklyDebriefFacts,
) -> WeeklyDebrief:
    """Construit le bilan objectif d'une semaine terminée."""

    _validate_facts(facts)

    completion_ratio = _ratio(
        facts.completed_sessions,
        facts.planned_sessions,
    )
    duration_ratio = _ratio(
        facts.actual_duration_minutes,
        facts.planned_duration_minutes,
    )
    load_ratio = _ratio(
        facts.actual_load,
        facts.planned_load,
    )

    adherence_score = _percentage_score(
        facts.completed_sessions,
        facts.planned_sessions,
    )
    duration_score = _bounded_score_from_ratio(duration_ratio)
    load_score = _bounded_score_from_ratio(load_ratio)

    key_sessions_score = _percentage_score(
        facts.key_sessions_completed,
        facts.key_sessions_planned,
    )
    intensity_score = _percentage_score(
        facts.compliant_intensity_sessions,
        facts.analyzed_intensity_sessions,
    )

    overall_score = _weighted_score(
        (
            (adherence_score, 0.30),
            (duration_score, 0.15),
            (load_score, 0.20),
            (key_sessions_score, 0.20),
            (intensity_score, 0.15),
        )
    )

    has_meaningful_plan = (
        facts.planned_sessions > 0
        or facts.planned_duration_minutes > 0
        or facts.planned_load > 0
    )

    strengths: list[str] = []
    warnings: list[str] = []

    if not has_meaningful_plan:
        verdict = WeeklyDebriefVerdict.UNKNOWN
        direction = WeeklyAdaptationDirection.OBSERVE
        headline = "Bilan hebdomadaire encore insuffisant."
        analysis = (
            "Aucune prescription hebdomadaire exploitable n'est disponible "
            "pour comparer objectivement le réalisé au prévu."
        )

        return WeeklyDebrief(
            week_start=facts.week_start,
            week_end=facts.week_end,
            verdict=verdict,
            adaptation_direction=direction,
            overall_score=None,
            adherence_score=adherence_score,
            duration_score=duration_score,
            load_score=load_score,
            key_sessions_score=key_sessions_score,
            intensity_score=intensity_score,
            completion_ratio=completion_ratio,
            duration_ratio=duration_ratio,
            load_ratio=load_ratio,
            headline=headline,
            analysis=analysis,
            strengths=(),
            warnings=(),
        )

    if (
        load_ratio is not None
        and load_ratio >= 1.20
    ):
        verdict = WeeklyDebriefVerdict.OVERLOAD
        direction = WeeklyAdaptationDirection.RECOVER
        warnings.append(
            "La charge réalisée dépasse nettement la charge prévue."
        )
    elif (
        overall_score is not None
        and overall_score >= 90
        and facts.skipped_sessions == 0
    ):
        verdict = WeeklyDebriefVerdict.VERY_PRODUCTIVE
        direction = WeeklyAdaptationDirection.PROGRESS
    elif overall_score is not None and overall_score >= 80:
        verdict = WeeklyDebriefVerdict.PRODUCTIVE
        direction = WeeklyAdaptationDirection.MAINTAIN
    elif overall_score is not None and overall_score >= 70:
        verdict = WeeklyDebriefVerdict.CORRECT
        direction = WeeklyAdaptationDirection.MAINTAIN
    elif overall_score is not None and overall_score >= 50:
        verdict = WeeklyDebriefVerdict.PARTIALLY_COMPLIANT
        direction = WeeklyAdaptationDirection.REDUCE
    else:
        verdict = WeeklyDebriefVerdict.INSUFFICIENT
        direction = WeeklyAdaptationDirection.RECOVER

    if (
        adherence_score is not None
        and adherence_score >= 90
    ):
        strengths.append(
            "L'assiduité au programme est excellente."
        )
    elif facts.skipped_sessions:
        warnings.append(
            f"{facts.skipped_sessions} séance(s) planifiée(s) "
            "n'ont pas été réalisée(s)."
        )

    if (
        key_sessions_score is not None
        and key_sessions_score == 100
    ):
        strengths.append(
            "Toutes les séances prioritaires ont été réalisées."
        )
    elif (
        key_sessions_score is not None
        and key_sessions_score < 100
    ):
        warnings.append(
            "Au moins une séance prioritaire n'a pas été réalisée."
        )

    if (
        intensity_score is not None
        and intensity_score >= 80
    ):
        strengths.append(
            "L'intensité des séances analysées est globalement conforme."
        )
    elif (
        intensity_score is not None
        and intensity_score < 60
    ):
        warnings.append(
            "L'intensité des séances analysées s'écarte régulièrement "
            "des objectifs."
        )

    if (
        duration_ratio is not None
        and 0.90 <= duration_ratio <= 1.10
    ):
        strengths.append(
            "Le temps d'entraînement réalisé est proche du volume prévu."
        )
    elif duration_ratio is not None and duration_ratio < 0.80:
        warnings.append(
            "Le temps d'entraînement réalisé est nettement inférieur "
            "au volume prévu."
        )
    elif duration_ratio is not None and duration_ratio > 1.20:
        warnings.append(
            "Le temps d'entraînement réalisé dépasse nettement "
            "le volume prévu."
        )

    if facts.supplementary_sessions:
        warnings.append(
            f"{facts.supplementary_sessions} séance(s) supplémentaire(s) "
            "ont été enregistrée(s) hors programme."
        )

    headline_by_verdict = {
        WeeklyDebriefVerdict.VERY_PRODUCTIVE:
            "Semaine très productive et conforme aux objectifs.",
        WeeklyDebriefVerdict.PRODUCTIVE:
            "Semaine productive et globalement conforme.",
        WeeklyDebriefVerdict.CORRECT:
            "Semaine correcte, avec quelques écarts maîtrisés.",
        WeeklyDebriefVerdict.PARTIALLY_COMPLIANT:
            "Semaine partiellement conforme au programme.",
        WeeklyDebriefVerdict.INSUFFICIENT:
            "Semaine insuffisamment conforme aux objectifs.",
        WeeklyDebriefVerdict.OVERLOAD:
            "Semaine en surcharge par rapport au programme.",
        WeeklyDebriefVerdict.UNKNOWN:
            "Bilan hebdomadaire encore insuffisant.",
    }

    headline = headline_by_verdict[verdict]

    score_label = (
        f"{overall_score}/100"
        if overall_score is not None
        else "non calculable"
    )

    analysis = (
        f"Conformité globale : {score_label}. "
        f"Séances réalisées : {facts.completed_sessions}/"
        f"{facts.planned_sessions}. "
        f"Temps réalisé : {facts.actual_duration_minutes} min sur "
        f"{facts.planned_duration_minutes} min prévues "
        f"({_format_ratio(duration_ratio)}). "
        f"Charge réalisée : {facts.actual_load:.1f} sur "
        f"{facts.planned_load:.1f} prévue "
        f"({_format_ratio(load_ratio)})."
    )

    return WeeklyDebrief(
        week_start=facts.week_start,
        week_end=facts.week_end,
        verdict=verdict,
        adaptation_direction=direction,
        overall_score=overall_score,
        adherence_score=adherence_score,
        duration_score=duration_score,
        load_score=load_score,
        key_sessions_score=key_sessions_score,
        intensity_score=intensity_score,
        completion_ratio=completion_ratio,
        duration_ratio=duration_ratio,
        load_ratio=load_ratio,
        headline=headline,
        analysis=analysis,
        strengths=tuple(strengths),
        warnings=tuple(warnings),
    )
