from dataclasses import dataclass
from typing import Literal

from opencoach.models import TrainingSession
from opencoach.training import normalize_intensity

from .candidates import TrainingDayCandidate
from .session_placement import (
    HARD_INTENSITIES,
    SessionPlacementContext,
)


RuleSeverity = Literal[
    "hard",
    "soft",
]


@dataclass(frozen=True)
class PlacementRuleResult:
    """Résultat explicable d'une règle de placement."""

    rule_id: str
    severity: RuleSeverity

    violated: bool
    score_adjustment: int

    reason: str


def evaluate_placement_rules(
    *,
    context: SessionPlacementContext,
    candidate: TrainingDayCandidate,
) -> tuple[PlacementRuleResult, ...]:
    """Évalue les règles applicables à un candidat."""

    results = [
        _same_day_session_rule(
            context=context,
            candidate=candidate,
        ),
        _previous_day_hard_rule(
            context=context,
            candidate=candidate,
        ),
        _next_day_hard_rule(
            context=context,
            candidate=candidate,
        ),
        _duration_limit_rule(
            context=context,
            candidate=candidate,
        ),
    ]

    return tuple(results)


def _same_day_session_rule(
    *,
    context: SessionPlacementContext,
    candidate: TrainingDayCandidate,
) -> PlacementRuleResult:
    sessions = _sessions_on_date(
        context.existing_sessions,
        candidate.date,
    )

    violated = bool(sessions)

    return PlacementRuleResult(
        rule_id="existing_session_same_day",
        severity="soft",
        violated=violated,
        score_adjustment=(
            -35
            if violated
            else 0
        ),
        reason=(
            "Une autre séance est déjà prévue ce jour."
        ),
    )


def _previous_day_hard_rule(
    *,
    context: SessionPlacementContext,
    candidate: TrainingDayCandidate,
) -> PlacementRuleResult:
    candidate_session_hard = _is_hard(
        context.session
    )

    previous_sessions = _sessions_at_offset(
        sessions=context.existing_sessions,
        candidate_date=candidate.date,
        offset=-1,
    )

    violated = (
        candidate_session_hard
        and any(
            _is_hard(session)
            for session in previous_sessions
        )
    )

    return PlacementRuleResult(
        rule_id="hard_session_previous_day",
        severity="hard",
        violated=violated,
        score_adjustment=0,
        reason=(
            "Séance intense déjà prévue la veille."
        ),
    )


def _next_day_hard_rule(
    *,
    context: SessionPlacementContext,
    candidate: TrainingDayCandidate,
) -> PlacementRuleResult:
    candidate_session_hard = _is_hard(
        context.session
    )

    next_sessions = _sessions_at_offset(
        sessions=context.existing_sessions,
        candidate_date=candidate.date,
        offset=1,
    )

    violated = (
        candidate_session_hard
        and any(
            _is_hard(session)
            for session in next_sessions
        )
    )

    return PlacementRuleResult(
        rule_id="hard_session_next_day",
        severity="hard",
        violated=violated,
        score_adjustment=0,
        reason=(
            "Séance intense déjà prévue le lendemain."
        ),
    )


def _duration_limit_rule(
    *,
    context: SessionPlacementContext,
    candidate: TrainingDayCandidate,
) -> PlacementRuleResult:
    violated = (
        candidate.max_duration_minutes
        is not None
        and context.session.duration_minutes
        > candidate.max_duration_minutes
    )

    return PlacementRuleResult(
        rule_id="duration_limit",
        severity="hard",
        violated=violated,
        score_adjustment=0,
        reason=(
            "Durée prévue supérieure à la disponibilité du jour."
        ),
    )


def _sessions_on_date(
    sessions: tuple[TrainingSession, ...],
    target_date,
) -> tuple[TrainingSession, ...]:
    return tuple(
        session
        for session in sessions
        if session.date == target_date
    )


def _sessions_at_offset(
    *,
    sessions: tuple[TrainingSession, ...],
    candidate_date,
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
