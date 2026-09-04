"""Évaluation d'un déplacement volontaire de séance.

Ce module est volontairement pur :

- aucune lecture SQL ;
- aucune écriture SQL ;
- aucune dépendance FastAPI ;
- aucune décision automatique à la place de l'athlète.

Il évalue chacun des jours de la semaine courante et fournit un
score explicable de 0 à 100.

Le score représente la qualité relative du placement selon les
règles OpenCoach. Il ne constitue pas une probabilité scientifique.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

from opencoach.models import (
    TrainingSession,
)
from opencoach.planning.athlete.availability import (
    DayAvailability,
)
from opencoach.planning.athlete.weekly_availability import (
    WeeklyAvailability,
)
from opencoach.training import (
    normalize_intensity,
)


SessionLoadClass = Literal[
    "rest",
    "easy",
    "strength",
    "quality",
    "long",
    "test",
    "other",
]

MoveRecommendationLevel = Literal[
    "current",
    "excellent",
    "good",
    "possible",
    "discouraged",
    "impossible",
]


MAJOR_CLASSES = {
    "quality",
    "long",
    "test",
}


@dataclass(
    frozen=True,
    slots=True,
)
class SessionMoveDayEvaluation:
    """Évaluation d'un jour de destination."""

    date: date

    score: int

    selectable: bool
    current: bool

    level: MoveRecommendationLevel

    recommended: bool

    reasons: tuple[
        str,
        ...,
    ]

    blocking_reasons: tuple[
        str,
        ...,
    ]


@dataclass(
    frozen=True,
    slots=True,
)
class SessionMovePlan:
    """Résultat complet présenté ensuite à l'athlète."""

    source_date: date

    week_start: date
    week_end: date

    best_date: date | None

    days: tuple[
        SessionMoveDayEvaluation,
        ...,
    ]


class ManualSessionMoveError(
    ValueError
):
    """Le déplacement ne peut pas être évalué."""


def classify_session_load(
    session: TrainingSession,
) -> SessionLoadClass:
    """Classe une séance selon son impact sur le placement."""

    session_type = (
        session.type
        .strip()
        .lower()
    )

    sport_type = (
        session.sport_type
        .strip()
        .lower()
    )

    if session_type == "rest":
        return "rest"

    if (
        session_type
        == "physiological_test"
    ):
        return "test"

    if session_type in {
        "long",
        "long_endurance",
    }:
        return "long"

    # Le type métier OpenCoach est prioritaire sur sport_type.
    #
    # Une séance adaptée peut conserver temporairement un sport_type
    # historique alors que son type a changé. Le moteur de placement
    # doit donc d'abord interpréter la prescription actuelle.
    if session_type.startswith(
        "strength"
    ):
        return "strength"

    if session_type in {
        "interval",
        "threshold",
        "vo2max",
        "speed_development",
        "tempo",
    }:
        return "quality"

    if session_type in {
        "easy",
        "recovery",
        "aerobic_easy",
        "trail",
        "supplementary",
    }:
        return "easy"

    intensity = (
        normalize_intensity(
            session.intensity
        )
    )

    if intensity in {
        "hard",
        "very_hard",
    }:
        return "quality"

    # Fallback seulement lorsqu'aucun type métier explicite
    # n'a permis de classifier la séance.
    if sport_type in {
        "strength",
        "strength_training",
        "weight_training",
    }:
        return "strength"

    if intensity in {
        "easy",
        "very_easy",
        "moderate",
    }:
        return "easy"

    return "other"


def evaluate_manual_session_move(
    *,
    session: TrainingSession,
    week: WeeklyAvailability,
    existing_sessions: tuple[
        TrainingSession,
        ...,
    ],
    reference_date: date,
) -> SessionMovePlan:
    """Évalue les sept jours de la semaine pour un déplacement.

    Règles structurantes :

    - uniquement une séance ``planned`` ;
    - uniquement la semaine courante ;
    - aucun jour déjà passé ;
    - disponibilité athlète respectée ;
    - durée maximale respectée ;
    - aucune séance importante superposée ;
    - récupération autour des grosses séances prise en compte ;
    - l'athlète conserve toujours la décision finale.
    """

    if session.status != "planned":
        raise ManualSessionMoveError(
            "Seule une séance planifiée "
            "peut être déplacée."
        )

    if session.activity_id is not None:
        raise ManualSessionMoveError(
            "Une séance déjà liée à une activité "
            "ne peut pas être déplacée."
        )

    expected_week_start = (
        session.date
        - _days(
            session.date.weekday()
        )
    )

    expected_week_end = (
        expected_week_start
        + _days(6)
    )

    if (
        week.start_date
        != expected_week_start
        or week.end_date
        != expected_week_end
    ):
        raise ManualSessionMoveError(
            "La disponibilité fournie ne correspond "
            "pas à la semaine de la séance."
        )

    if not (
        week.start_date
        <= reference_date
        <= week.end_date
    ):
        raise ManualSessionMoveError(
            "Une séance ne peut être déplacée "
            "que pendant sa semaine en cours."
        )

    evaluations = [
        _evaluate_day(
            session=session,
            day=day,
            existing_sessions=(
                existing_sessions
            ),
            reference_date=(
                reference_date
            ),
        )
        for day in week.days
    ]

    selectable = [
        item
        for item in evaluations
        if item.selectable
    ]

    best = (
        max(
            selectable,
            key=lambda item: (
                item.score,
                -abs(
                    (
                        item.date
                        - session.date
                    ).days
                ),
                -item.date.toordinal(),
            ),
        )
        if selectable
        else None
    )

    result = tuple(
        SessionMoveDayEvaluation(
            date=item.date,
            score=item.score,
            selectable=item.selectable,
            current=item.current,
            level=item.level,
            recommended=(
                best is not None
                and item.date
                == best.date
            ),
            reasons=item.reasons,
            blocking_reasons=(
                item.blocking_reasons
            ),
        )
        for item in evaluations
    )

    return SessionMovePlan(
        source_date=session.date,
        week_start=week.start_date,
        week_end=week.end_date,
        best_date=(
            best.date
            if best is not None
            else None
        ),
        days=result,
    )


def _evaluate_day(
    *,
    session: TrainingSession,
    day: DayAvailability,
    existing_sessions: tuple[
        TrainingSession,
        ...,
    ],
    reference_date: date,
) -> SessionMoveDayEvaluation:
    """Évalue un seul jour."""

    if day.date == session.date:
        return SessionMoveDayEvaluation(
            date=day.date,
            score=100,
            selectable=False,
            current=True,
            level="current",
            recommended=False,
            reasons=(
                "Emplacement actuel de la séance.",
            ),
            blocking_reasons=(),
        )

    blocking: list[str] = []
    reasons: list[str] = []

    if day.date < reference_date:
        blocking.append(
            "Cette journée est déjà passée."
        )

    if not day.training_allowed:
        blocking.append(
            "L'athlète est indisponible ce jour."
        )

    is_running = (
        session.sport_type
        .strip()
        .lower()
        == "run"
    )

    if (
        is_running
        and not day.running_allowed
    ):
        blocking.append(
            "La course à pied n'est pas autorisée "
            "ce jour."
        )

    if (
        not is_running
        and not day.cross_training_allowed
    ):
        blocking.append(
            "L'entraînement croisé n'est pas "
            "autorisé ce jour."
        )

    if (
        day.max_duration_minutes
        is not None
        and session.duration_minutes
        > day.max_duration_minutes
    ):
        blocking.append(
            "La durée de la séance dépasse "
            "la disponibilité de cette journée."
        )

    other_sessions = tuple(
        item
        for item in existing_sessions
        if (
            item.id != session.id
            and item.status
            == "planned"
        )
    )

    same_day = tuple(
        item
        for item in other_sessions
        if item.date == day.date
    )

    previous_day = tuple(
        item
        for item in other_sessions
        if (
            day.date
            - item.date
        ).days == 1
    )

    next_day = tuple(
        item
        for item in other_sessions
        if (
            item.date
            - day.date
        ).days == 1
    )

    moving_class = (
        classify_session_load(
            session
        )
    )

    same_classes = tuple(
        classify_session_load(
            item
        )
        for item in same_day
    )

    previous_classes = tuple(
        classify_session_load(
            item
        )
        for item in previous_day
    )

    next_classes = tuple(
        classify_session_load(
            item
        )
        for item in next_day
    )

    # --------------------------------------------------------
    # Conflits bloquants le même jour
    # --------------------------------------------------------

    if (
        moving_class in MAJOR_CLASSES
        and any(
            value != "rest"
            for value in same_classes
        )
    ):
        blocking.append(
            "Une séance importante ne doit pas "
            "être ajoutée à une journée déjà chargée."
        )

    if (
        moving_class == "strength"
        and any(
            value in MAJOR_CLASSES
            for value in same_classes
        )
    ):
        blocking.append(
            "Le renforcement ne doit pas être "
            "placé le même jour qu'une grosse séance."
        )

    # --------------------------------------------------------
    # Grosses séances adjacentes
    # --------------------------------------------------------

    adjacent_major = (
        sum(
            value in MAJOR_CLASSES
            for value
            in previous_classes
        )
        + sum(
            value in MAJOR_CLASSES
            for value
            in next_classes
        )
    )

    if (
        moving_class in MAJOR_CLASSES
        and adjacent_major
    ):
        blocking.append(
            "Une grosse séance est déjà prévue "
            "la veille ou le lendemain."
        )

    if blocking:
        return SessionMoveDayEvaluation(
            date=day.date,
            score=0,
            selectable=False,
            current=False,
            level="impossible",
            recommended=False,
            reasons=tuple(reasons),
            blocking_reasons=tuple(
                dict.fromkeys(
                    blocking
                )
            ),
        )

    # --------------------------------------------------------
    # Score initial
    # --------------------------------------------------------

    score = 82

    reasons.append(
        "Journée compatible avec les contraintes "
        "de base."
    )

    # --------------------------------------------------------
    # Disponibilité
    # --------------------------------------------------------

    if day.preferred:
        score += 8
        reasons.append(
            "Jour habituel préféré par l'athlète."
        )
    else:
        score -= 4
        reasons.append(
            "Ce n'est pas un jour habituel "
            "d'entraînement."
        )

    if (
        day.status
        == "available_override"
    ):
        score += 6
        reasons.append(
            "Disponibilité exceptionnelle confirmée."
        )

    if day.status == "limited":
        score -= 12
        reasons.append(
            "La disponibilité de la journée "
            "est limitée."
        )

    if day.requires_confirmation:
        score -= 3

    # --------------------------------------------------------
    # Écart avec la date originale
    #
    # Contrairement au moteur historique, on ne veut pas que
    # la proximité écrase la qualité sportive du placement.
    # --------------------------------------------------------

    distance_days = abs(
        (
            day.date
            - session.date
        ).days
    )

    score -= (
        distance_days
        * 4
    )

    reasons.append(
        f"Déplacement de {distance_days} jour(s) "
        "par rapport au planning initial."
    )

    # --------------------------------------------------------
    # Journée elle-même
    # --------------------------------------------------------

    meaningful_same_day = tuple(
        value
        for value in same_classes
        if value != "rest"
    )

    if not meaningful_same_day:
        score += 9
        reasons.append(
            "Aucune autre séance significative "
            "n'est prévue ce jour."
        )

    elif (
        moving_class == "strength"
        and all(
            value == "easy"
            for value
            in meaningful_same_day
        )
    ):
        score -= 12
        reasons.append(
            "Un footing facile est déjà prévu : "
            "le cumul reste possible mais augmente "
            "la charge de la journée."
        )

    elif (
        moving_class == "easy"
        and all(
            value == "strength"
            for value
            in meaningful_same_day
        )
    ):
        score -= 10
        reasons.append(
            "Un renforcement est déjà prévu "
            "ce jour."
        )

    else:
        score -= 22
        reasons.append(
            "Une autre séance est déjà prévue "
            "ce jour."
        )

    # --------------------------------------------------------
    # Séances structurantes la veille / lendemain
    # --------------------------------------------------------

    if moving_class == "strength":
        major_previous = any(
            value in MAJOR_CLASSES
            for value in previous_classes
        )

        major_next = any(
            value in MAJOR_CLASSES
            for value in next_classes
        )

        if major_previous and major_next:
            score -= 45
            reasons.append(
                "Le renforcement serait placé entre "
                "deux grosses séances : récupération "
                "très défavorable."
            )

        elif major_next:
            score -= 38
            reasons.append(
                "Une grosse séance est prévue le lendemain : "
                "le renforcement risque de compromettre "
                "sa qualité."
            )

        elif major_previous:
            score -= 20
            reasons.append(
                "Une grosse séance est prévue la veille : "
                "le renforcement reste possible mais "
                "la récupération est moins favorable."
            )

        else:
            score += 7
            reasons.append(
                "Le renforcement est suffisamment "
                "éloigné des grosses séances voisines."
            )

    elif moving_class == "easy":
        if adjacent_major:
            score -= 5
            reasons.append(
                "Une grosse séance est proche, "
                "mais une séance facile reste compatible."
            )
        else:
            score += 5
            reasons.append(
                "Bonne séparation avec les séances "
                "importantes."
            )

    elif moving_class in {
        "other",
    }:
        if adjacent_major:
            score -= 15
            reasons.append(
                "Une grosse séance est proche."
            )

    # --------------------------------------------------------
    # Bornage du score
    # --------------------------------------------------------

    score = max(
        1,
        min(
            100,
            score,
        ),
    )

    level = (
        _recommendation_level(
            score
        )
    )

    return SessionMoveDayEvaluation(
        date=day.date,
        score=score,
        selectable=True,
        current=False,
        level=level,
        recommended=False,
        reasons=tuple(
            dict.fromkeys(
                reasons
            )
        ),
        blocking_reasons=(),
    )


def _recommendation_level(
    score: int,
) -> MoveRecommendationLevel:
    if score >= 85:
        return "excellent"

    if score >= 70:
        return "good"

    if score >= 50:
        return "possible"

    return "discouraged"


def _days(
    value: int,
):
    """Évite de répéter l'import dans les règles de semaine."""

    from datetime import timedelta

    return timedelta(
        days=value
    )
