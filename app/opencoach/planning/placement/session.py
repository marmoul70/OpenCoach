from dataclasses import dataclass
from datetime import date

from opencoach.models import TrainingSession
from opencoach.training import normalize_intensity

from opencoach.planning.athlete.weekly_availability import WeeklyAvailability


HARD_INTENSITIES = {
    "hard",
    "very_hard",
}


@dataclass(frozen=True)
class SessionPlacementContext:
    """Contexte nécessaire pour évaluer le placement d'une séance."""

    session: TrainingSession
    original_date: date

    week: WeeklyAvailability

    existing_sessions: tuple[TrainingSession, ...]

    previous_session: TrainingSession | None
    next_session: TrainingSession | None

    previous_day_hard: bool
    next_day_hard: bool

    include_original_date: bool = False


def build_session_placement_context(
    *,
    session: TrainingSession,
    week: WeeklyAvailability,
    existing_sessions: tuple[TrainingSession, ...],
    include_original_date: bool = False,
) -> SessionPlacementContext:
    """Construit le contexte autour d'une séance à replacer."""

    if session.id is None:
        other_sessions = existing_sessions
    else:
        other_sessions = tuple(
            item
            for item in existing_sessions
            if item.id != session.id
        )

    previous_session = _find_previous_session(
        session_date=session.date,
        sessions=other_sessions,
    )

    next_session = _find_next_session(
        session_date=session.date,
        sessions=other_sessions,
    )

    previous_day_hard = any(
        _is_hard_session(item)
        and (
            session.date - item.date
        ).days == 1
        for item in other_sessions
    )

    next_day_hard = any(
        _is_hard_session(item)
        and (
            item.date - session.date
        ).days == 1
        for item in other_sessions
    )

    return SessionPlacementContext(
        session=session,
        original_date=session.date,
        week=week,
        existing_sessions=other_sessions,
        previous_session=previous_session,
        next_session=next_session,
        previous_day_hard=previous_day_hard,
        next_day_hard=next_day_hard,
        include_original_date=include_original_date,
    )


def _find_previous_session(
    *,
    session_date: date,
    sessions: tuple[TrainingSession, ...],
) -> TrainingSession | None:
    previous_sessions = [
        session
        for session in sessions
        if session.date < session_date
    ]

    if not previous_sessions:
        return None

    return max(
        previous_sessions,
        key=lambda session: session.date,
    )


def _find_next_session(
    *,
    session_date: date,
    sessions: tuple[TrainingSession, ...],
) -> TrainingSession | None:
    next_sessions = [
        session
        for session in sessions
        if session.date > session_date
    ]

    if not next_sessions:
        return None

    return min(
        next_sessions,
        key=lambda session: session.date,
    )


def _is_hard_session(
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
