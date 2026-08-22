from dataclasses import dataclass
from datetime import date

from opencoach.models import TrainingSession
from opencoach.training import normalize_intensity

from .candidates import (
    TrainingDayCandidate,
    rank_training_day_candidates,
)
from .session_placement import (
    HARD_INTENSITIES,
    SessionPlacementContext,
)


@dataclass(frozen=True)
class SessionPlacementCandidate:
    """Évaluation d'un jour candidat pour une séance donnée."""

    date: date

    calendar_score: int
    placement_score: int

    preferred: bool
    requires_confirmation: bool

    running_allowed: bool
    cross_training_allowed: bool
    max_duration_minutes: int | None

    reasons: tuple[str, ...]


def rank_session_placement_candidates(
    *,
    context: SessionPlacementContext,
) -> tuple[SessionPlacementCandidate, ...]:
    """Classe les jours candidats selon calendrier et séances voisines."""

    for_running = (
        context.session.sport_type
        == "run"
    )

    calendar_candidates = (
        rank_training_day_candidates(
            week=context.week,
            original_date=context.original_date,
            for_running=for_running,
        )
    )

    candidates = tuple(
        _score_candidate(
            context=context,
            candidate=candidate,
        )
        for candidate in calendar_candidates
    )

    return tuple(
        sorted(
            candidates,
            key=lambda candidate: (
                -candidate.placement_score,
                -candidate.calendar_score,
                candidate.date,
            ),
        )
    )


def _score_candidate(
    *,
    context: SessionPlacementContext,
    candidate: TrainingDayCandidate,
) -> SessionPlacementCandidate:
    score = candidate.score

    reasons = list(
        candidate.reasons
    )

    session_is_hard = _is_hard(
        context.session
    )

    sessions_previous_day = (
        _sessions_at_offset(
            sessions=context.existing_sessions,
            candidate_date=candidate.date,
            offset=-1,
        )
    )

    sessions_same_day = (
        _sessions_at_offset(
            sessions=context.existing_sessions,
            candidate_date=candidate.date,
            offset=0,
        )
    )

    sessions_next_day = (
        _sessions_at_offset(
            sessions=context.existing_sessions,
            candidate_date=candidate.date,
            offset=1,
        )
    )

    if sessions_same_day:
        score -= 35

        reasons.append(
            "Une autre séance est déjà prévue ce jour."
        )

    if session_is_hard:
        if any(
            _is_hard(session)
            for session in sessions_previous_day
        ):
            score -= 45

            reasons.append(
                "Séance intense déjà prévue la veille."
            )

        if any(
            _is_hard(session)
            for session in sessions_next_day
        ):
            score -= 45

            reasons.append(
                "Séance intense déjà prévue le lendemain."
            )

    if (
        candidate.max_duration_minutes
        is not None
        and context.session.duration_minutes
        > candidate.max_duration_minutes
    ):
        score -= 50

        reasons.append(
            "Durée prévue supérieure à la disponibilité du jour."
        )

    return SessionPlacementCandidate(
        date=candidate.date,
        calendar_score=candidate.score,
        placement_score=score,
        preferred=candidate.preferred,
        requires_confirmation=(
            candidate.requires_confirmation
        ),
        running_allowed=(
            candidate.running_allowed
        ),
        cross_training_allowed=(
            candidate.cross_training_allowed
        ),
        max_duration_minutes=(
            candidate.max_duration_minutes
        ),
        reasons=tuple(reasons),
    )


def _sessions_at_offset(
    *,
    sessions: tuple[TrainingSession, ...],
    candidate_date: date,
    offset: int,
) -> tuple[TrainingSession, ...]:
    return tuple(
        session
        for session in sessions
        if (
            session.date
            - candidate_date
        ).days == offset
    )


def _is_hard(
    session: TrainingSession,
) -> bool:
    if session.type == "rest":
        return False

    return (
        normalize_intensity(
            session.intensity
        )
        in HARD_INTENSITIES
    )
