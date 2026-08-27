"""Proposition de report après annulation quotidienne.

Ce module ne déplace aucune séance.

Il analyse une séance déclarée ``skipped`` après un check-in
quotidien et recherche, lorsque cela est pertinent, le meilleur
créneau strictement futur dans la semaine courante.

Le moteur générique de placement reste inchangé : il continue
d'autoriser les déplacements avant ou après la date initiale pour
les scénarios de replanification anticipée.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from opencoach.models import TrainingSession
from opencoach.planning import (
    build_session_placement_context,
    build_session_placement_result,
    rank_session_placement_candidates,
)
from opencoach.planning.athlete.weekly_availability import (
    WeeklyAvailability,
)
from opencoach.training import (
    normalize_intensity,
)


@dataclass(frozen=True, slots=True)
class DailySessionReschedulingProposal:
    """Proposition de report soumise à l'athlète."""

    original_session: TrainingSession

    suggested_date: date

    requires_confirmation: bool

    reasons: tuple[
        str,
        ...
    ]


def propose_daily_session_rescheduling(
    *,
    session: TrainingSession,
    week: WeeklyAvailability,
    existing_sessions: tuple[
        TrainingSession,
        ...
    ],
    reference_date: date,
) -> DailySessionReschedulingProposal | None:
    """Propose un report futur lorsqu'il est pertinent et sûr."""

    if session.status != "skipped":
        return None

    if session.activity_id is not None:
        return None

    if not _should_reschedule(
        session
    ):
        return None

    context = (
        build_session_placement_context(
            session=session,
            week=week,
            existing_sessions=(
                existing_sessions
            ),
        )
    )

    ranked_candidates = (
        rank_session_placement_candidates(
            context=context,
        )
    )

    future_candidates = tuple(
        candidate
        for candidate in ranked_candidates
        if candidate.date > reference_date
    )

    result = (
        build_session_placement_result(
            future_candidates
        )
    )

    candidate = result.best_candidate

    if candidate is None:
        return None

    return DailySessionReschedulingProposal(
        original_session=session,
        suggested_date=(
            candidate.date
        ),
        requires_confirmation=(
            candidate.requires_confirmation
        ),
        reasons=(
            candidate.reasons
        ),
    )


def _should_reschedule(
    session: TrainingSession,
) -> bool:
    """Détermine si la séance mérite une proposition de report."""

    if session.type == "long_endurance":
        return True

    intensity = normalize_intensity(
        session.intensity
    )

    return intensity in {
        "hard",
        "very_hard",
    }
