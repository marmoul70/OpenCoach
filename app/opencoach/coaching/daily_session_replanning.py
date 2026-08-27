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

    unchanged_candidate = (
        _find_unchanged_candidate(
            session=session,
            week=week,
            existing_sessions=(
                existing_sessions
            ),
            reference_date=reference_date,
        )
    )

    unchanged_option = (
        _build_unchanged_option(
            session=session,
            candidate=unchanged_candidate,
        )
        if unchanged_candidate is not None
        else None
    )

    adapted_session = (
        _build_adapted_session(
            session
        )
    )

    adapted_candidate = (
        _find_adapted_candidate(
            session=adapted_session,
            week=week,
            existing_sessions=(
                existing_sessions
            ),
            reference_date=reference_date,
        )
        if adapted_session is not None
        else None
    )

    adapted_option = (
        _build_adapted_option(
            session=adapted_session,
            candidate=adapted_candidate,
        )
        if (
            adapted_session is not None
            and adapted_candidate is not None
        )
        else None
    )

    options = [
        cancel_option,
    ]

    if unchanged_option is not None:
        options.append(
            unchanged_option
        )

    if adapted_option is not None:
        options.append(
            adapted_option
        )

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


def _find_unchanged_candidate(
    *,
    session: TrainingSession,
    week: WeeklyAvailability,
    existing_sessions: tuple[
        TrainingSession,
        ...,
    ],
    reference_date: date,
) -> SessionPlacementCandidate | None:
    """Cherche un jour futur pour la séance intacte."""

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
        return None

    return (
        _prefer_free_day(
            acceptable
        )[0]
    )


def _find_adapted_candidate(
    *,
    session: TrainingSession,
    week: WeeklyAvailability,
    existing_sessions: tuple[
        TrainingSession,
        ...,
    ],
    reference_date: date,
) -> SessionPlacementCandidate | None:
    """Cherche un jour futur pour la version adaptée."""

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

    eligible = tuple(
        candidate
        for candidate in candidates
        if candidate.eligible
    )

    if not eligible:
        return None

    return (
        _prefer_free_day(
            eligible
        )[0]
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
    """Évite de cumuler deux séances le même jour."""

    free = tuple(
        candidate
        for candidate in candidates
        if not _has_same_day_conflict(
            candidate
        )
    )

    return (
        free
        if free
        else candidates
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
    """Choisit la recommandation OpenCoach."""

    unchanged = next(
        (
            option
            for option in options
            if (
                option.action
                is DailyReplanningAction
                .MOVE_UNCHANGED
            )
        ),
        None,
    )

    adapted = next(
        (
            option
            for option in options
            if (
                option.action
                is DailyReplanningAction
                .MOVE_ADAPTED
            )
        ),
        None,
    )

    if (
        adapted is not None
        and (
            unchanged is None
            or unchanged.risk
            is DailyReplanningRisk.HIGH
        )
    ):
        recommended_action = (
            DailyReplanningAction
            .MOVE_ADAPTED
        )

    elif unchanged is not None:
        recommended_action = (
            DailyReplanningAction
            .MOVE_UNCHANGED
        )

    elif adapted is not None:
        recommended_action = (
            DailyReplanningAction
            .MOVE_ADAPTED
        )

    else:
        recommended_action = (
            DailyReplanningAction.CANCEL
        )

    return [
        replace(
            option,
            recommended=(
                option.action
                is recommended_action
            ),
        )
        for option in options
    ]
