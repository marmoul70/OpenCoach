"""Replanification déterministe d'une séance quotidienne annulée.

Le moteur propose plusieurs choix à l'athlète :

- annuler définitivement ;
- déplacer la séance sans modification ;
- déplacer une version adaptée.

Aucune modification n'est persistée ici.
"""

from __future__ import annotations

from dataclasses import (
    dataclass,
    replace,
)
from datetime import date
from enum import StrEnum

from opencoach.models import (
    TrainingSession,
)
from opencoach.planning import (
    SessionPlacementCandidate,
    build_session_placement_context,
    rank_session_placement_candidates,
)
from opencoach.planning.athlete.weekly_availability import (
    WeeklyAvailability,
)
from opencoach.training import (
    normalize_intensity,
)


class DailyReplanningAction(StrEnum):
    """Actions possibles après annulation."""

    CANCEL = "cancel"
    MOVE_UNCHANGED = "move_unchanged"
    MOVE_ADAPTED = "move_adapted"


class DailyReplanningRisk(StrEnum):
    """Niveau de risque relatif."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


@dataclass(
    frozen=True,
    slots=True,
)
class DailySessionReplanningOption:
    """Option proposée à l'athlète."""

    action: DailyReplanningAction

    target_date: date | None

    session: TrainingSession | None

    risk: DailyReplanningRisk

    recommended: bool

    requires_confirmation: bool

    reasons: tuple[
        str,
        ...,
    ]


@dataclass(
    frozen=True,
    slots=True,
)
class DailySessionReplanningProposal:
    """Ensemble des choix de replanification."""

    original_session: TrainingSession

    options: tuple[
        DailySessionReplanningOption,
        ...,
    ]

    @property
    def recommended_option(
        self,
    ) -> DailySessionReplanningOption:
        """Retourne l'unique recommandation OpenCoach."""

        recommended = tuple(
            option
            for option in self.options
            if option.recommended
        )

        if len(recommended) != 1:
            raise RuntimeError(
                "Une proposition doit posséder "
                "exactement une option recommandée."
            )

        return recommended[0]


def propose_daily_session_replanning(
    *,
    session: TrainingSession,
    week: WeeklyAvailability,
    existing_sessions: tuple[
        TrainingSession,
        ...,
    ],
    reference_date: date,
) -> DailySessionReplanningProposal | None:
    """Construit les choix possibles après annulation."""

    if session.status != "skipped":
        return None

    if session.activity_id is not None:
        return None

    cancel_option = (
        DailySessionReplanningOption(
            action=DailyReplanningAction.CANCEL,
            target_date=None,
            session=None,
            risk=DailyReplanningRisk.LOW,
            recommended=False,
            requires_confirmation=False,
            reasons=(
                "La séance reste annulée.",
                (
                    "La charge prévue de la semaine "
                    "sera réduite."
                ),
            ),
        )
    )

    unchanged_candidates = (
        _find_unchanged_candidates(
            session=session,
            week=week,
            existing_sessions=(
                existing_sessions
            ),
            reference_date=reference_date,
        )
    )

    unchanged_options = [
        _build_unchanged_option(
            session=session,
            candidate=candidate,
        )
        for candidate
        in unchanged_candidates
    ]

    adapted_session = (
        _build_adapted_session(
            session
        )
    )

    adapted_candidates = (
        _find_adapted_candidates(
            session=adapted_session,
            week=week,
            existing_sessions=(
                existing_sessions
            ),
            reference_date=reference_date,
        )
        if adapted_session is not None
        else ()
    )

    adapted_options = (
        [
            _build_adapted_option(
                session=adapted_session,
                candidate=candidate,
            )
            for candidate
            in adapted_candidates
        ]
        if adapted_session is not None
        else []
    )

    options = [
        cancel_option,
        *unchanged_options,
        *adapted_options,
    ]

    options = (
        _mark_recommended_option(
            options
        )
    )

    return DailySessionReplanningProposal(
        original_session=session,
        options=tuple(
            options
        ),
    )


def _find_unchanged_candidates(
    *,
    session: TrainingSession,
    week: WeeklyAvailability,
    existing_sessions: tuple[
        TrainingSession,
        ...,
    ],
    reference_date: date,
) -> tuple[
    SessionPlacementCandidate,
    ...,
]:
    """Retourne tous les jours futurs admissibles.

    Les jours libres restent prioritaires dans l'ordre,
    mais un jour déjà occupé peut rester proposé comme
    choix volontaire de l'athlète.
    """

    candidates = (
        _rank_future_candidates(
            session=session,
            week=week,
            existing_sessions=(
                existing_sessions
            ),
            reference_date=reference_date,
        )
    )

    acceptable = tuple(
        candidate
        for candidate in candidates
        if (
            candidate.eligible
            or _only_spacing_conflicts(
                candidate
            )
        )
    )

    if not acceptable:
        return ()

    return _prefer_free_day(
        acceptable
    )


def _find_adapted_candidates(
    *,
    session: TrainingSession,
    week: WeeklyAvailability,
    existing_sessions: tuple[
        TrainingSession,
        ...,
    ],
    reference_date: date,
) -> tuple[
    SessionPlacementCandidate,
    ...,
]:
    """Retourne les jours possibles pour la version adaptée.

    Une collision de densité ou de même jour peut rester
    négociable. Les vraies contraintes d'indisponibilité
    restent exclues par les règles non négociables.
    """

    candidates = (
        _rank_future_candidates(
            session=session,
            week=week,
            existing_sessions=(
                existing_sessions
            ),
            reference_date=reference_date,
        )
    )

    acceptable = tuple(
        candidate
        for candidate in candidates
        if (
            candidate.eligible
            or _only_spacing_conflicts(
                candidate
            )
        )
    )

    if not acceptable:
        return ()

    return _prefer_free_day(
        acceptable
    )


def _rank_future_candidates(
    *,
    session: TrainingSession,
    week: WeeklyAvailability,
    existing_sessions: tuple[
        TrainingSession,
        ...,
    ],
    reference_date: date,
) -> tuple[
    SessionPlacementCandidate,
    ...,
]:
    """Classe uniquement les jours futurs."""

    context = (
        build_session_placement_context(
            session=session,
            week=week,
            existing_sessions=(
                existing_sessions
            ),
        )
    )

    candidates = (
        rank_session_placement_candidates(
            context=context,
        )
    )

    return tuple(
        candidate
        for candidate in candidates
        if candidate.date > reference_date
    )


def _prefer_free_day(
    candidates: tuple[
        SessionPlacementCandidate,
        ...,
    ],
) -> tuple[
    SessionPlacementCandidate,
        ...,
]:
    """Préfère un jour libre sans interdire un cumul volontaire.

    Un jour contenant déjà une séance reste une option valide.

    OpenCoach doit :
    - recommander prioritairement les jours libres ;
    - conserver les jours occupés comme choix explicite ;
    - signaler le risque et demander confirmation si nécessaire.

    Une préférence de placement ne constitue donc pas une
    interdiction métier.
    """

    free = tuple(
        candidate
        for candidate in candidates
        if not _has_same_day_conflict(
            candidate
        )
    )

    occupied = tuple(
        candidate
        for candidate in candidates
        if _has_same_day_conflict(
            candidate
        )
    )

    return (
        *free,
        *occupied,
    )


def _has_same_day_conflict(
    candidate: SessionPlacementCandidate,
) -> bool:
    return any(
        (
            rule.rule_id
            == "existing_session_same_day"
            and rule.violated
        )
        for rule in candidate.rules
    )


def _only_spacing_conflicts(
    candidate: SessionPlacementCandidate,
) -> bool:
    """Autorise les conflits de densité comme choix volontaire."""

    hard_violations = tuple(
        rule
        for rule in candidate.rules
        if (
            rule.violated
            and rule.severity == "hard"
        )
    )

    if not hard_violations:
        return True

    negotiable = {
        "hard_session_previous_day",
        "hard_session_next_day",
        "existing_session_same_day",
    }

    return all(
        rule.rule_id in negotiable
        for rule in hard_violations
    )


def _build_unchanged_option(
    *,
    session: TrainingSession,
    candidate: SessionPlacementCandidate,
) -> DailySessionReplanningOption:
    """Déplacement sans modifier la séance."""

    spacing_conflict = any(
        (
            rule.violated
            and rule.rule_id
            in {
                "hard_session_previous_day",
                "hard_session_next_day",
            }
        )
        for rule in candidate.rules
    )

    same_day_conflict = (
        _has_same_day_conflict(
            candidate
        )
    )

    if spacing_conflict:
        risk = DailyReplanningRisk.HIGH

    elif (
        same_day_conflict
        or candidate.requires_confirmation
    ):
        risk = (
            DailyReplanningRisk.MODERATE
        )

    else:
        risk = DailyReplanningRisk.LOW

    return DailySessionReplanningOption(
        action=(
            DailyReplanningAction
            .MOVE_UNCHANGED
        ),
        target_date=candidate.date,
        session=replace(
            session,
            date=candidate.date,
            status="planned",
        ),
        risk=risk,
        recommended=False,
        requires_confirmation=(
            candidate.requires_confirmation
            or same_day_conflict
            or risk
            is DailyReplanningRisk.HIGH
        ),
        reasons=(
            (
                "La séance est déplacée "
                "sans modification."
            ),
            *candidate.reasons,
        ),
    )


def _build_adapted_option(
    *,
    session: TrainingSession,
    candidate: SessionPlacementCandidate,
) -> DailySessionReplanningOption:
    """Déplacement d'une version allégée."""

    risk = (
        DailyReplanningRisk.MODERATE
        if (
            _has_same_day_conflict(
                candidate
            )
            or candidate.requires_confirmation
        )
        else DailyReplanningRisk.LOW
    )

    return DailySessionReplanningOption(
        action=(
            DailyReplanningAction
            .MOVE_ADAPTED
        ),
        target_date=candidate.date,
        session=replace(
            session,
            date=candidate.date,
            status="planned",
        ),
        risk=risk,
        recommended=False,
        requires_confirmation=(
            candidate.requires_confirmation
            or _has_same_day_conflict(
                candidate
            )
        ),
        reasons=(
            (
                "La séance est allégée afin "
                "de préserver l'équilibre "
                "de la semaine."
            ),
            *candidate.reasons,
        ),
    )


def _build_adapted_session(
    session: TrainingSession,
) -> TrainingSession | None:
    """Construit une variante plus légère sans changer de modalité."""

    sport_type = (
        session.sport_type
        .strip()
        .lower()
    )

    session_type = (
        session.type
        .strip()
        .lower()
    )

    # --------------------------------------------------------
    # Renforcement
    # --------------------------------------------------------
    #
    # Une séance de force ne doit jamais devenir artificiellement
    # une séance de course.
    #
    if (
        sport_type
        in {
            "strength",
            "musculation",
        }
        or session_type.startswith(
            "strength"
        )
    ):
        reduced_duration = max(
            10,
            round(
                session.duration_minutes
                * 0.7
            ),
        )

        reduced_duration = min(
            reduced_duration,
            session.duration_minutes,
        )

        return replace(
            session,
            title=(
                f"{session.title} allégé"
            ),
            description=(
                "Séance de renforcement conservée "
                "mais allégée afin de limiter "
                "la densité de charge de la semaine."
            ),
            duration_minutes=(
                reduced_duration
            ),
            intensity="easy",
            heart_rate_zone=None,
        )

    intensity = normalize_intensity(
        session.intensity
    )

    # --------------------------------------------------------
    # Course qualitative
    # --------------------------------------------------------

    if (
        sport_type == "run"
        and intensity in {
            "hard",
            "very_hard",
        }
    ):
        return replace(
            session,
            type="aerobic_easy",
            title="Endurance facile adaptée",
            description=(
                "Séance qualitative remplacée "
                "par une endurance facile afin "
                "de préserver l'équilibre "
                "de la semaine."
            ),
            duration_minutes=min(
                session.duration_minutes,
                45,
            ),
            intensity="easy",
            heart_rate_zone=None,
        )

    if session.type == "long_endurance":
        return replace(
            session,
            title="Sortie endurance adaptée",
            description=(
                "Volume réduit afin de préserver "
                "la récupération de la semaine."
            ),
            duration_minutes=max(
                30,
                round(
                    session.duration_minutes
                    * 0.75
                ),
            ),
            intensity="easy",
            heart_rate_zone=None,
        )

    if session.duration_minutes > 40:
        return replace(
            session,
            title=f"{session.title} adaptée",
            description=(
                "Durée réduite afin de préserver "
                "l'équilibre de la semaine."
            ),
            duration_minutes=max(
                30,
                round(
                    session.duration_minutes
                    * 0.8
                ),
            ),
        )

    return None


def _mark_recommended_option(
    options: list[
        DailySessionReplanningOption
    ],
) -> list[
    DailySessionReplanningOption
]:
    """Choisit exactement une recommandation OpenCoach.

    Les options sont déjà ordonnées par qualité de
    placement : les jours libres précèdent les jours
    comportant un conflit de même journée.

    La recommandation privilégie :
    1. un déplacement intact à risque faible/modéré ;
    2. une version adaptée si l'intact est à risque élevé ;
    3. toute autre option de déplacement disponible ;
    4. l'annulation en dernier recours.
    """

    unchanged = tuple(
        option
        for option in options
        if (
            option.action
            is DailyReplanningAction
            .MOVE_UNCHANGED
        )
    )

    adapted = tuple(
        option
        for option in options
        if (
            option.action
            is DailyReplanningAction
            .MOVE_ADAPTED
        )
    )

    recommended_option = None

    best_unchanged = (
        unchanged[0]
        if unchanged
        else None
    )

    best_adapted = (
        adapted[0]
        if adapted
        else None
    )

    if (
        best_unchanged is not None
        and best_unchanged.risk
        is not DailyReplanningRisk.HIGH
    ):
        recommended_option = (
            best_unchanged
        )

    elif best_adapted is not None:
        recommended_option = (
            best_adapted
        )

    elif best_unchanged is not None:
        recommended_option = (
            best_unchanged
        )

    else:
        recommended_option = next(
            option
            for option in options
            if (
                option.action
                is DailyReplanningAction.CANCEL
            )
        )

    return [
        replace(
            option,
            recommended=(
                option
                is recommended_option
            ),
        )
        for option in options
    ]

