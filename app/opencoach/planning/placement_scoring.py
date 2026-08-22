from dataclasses import dataclass
from datetime import date

from .candidates import (
    TrainingDayCandidate,
    rank_training_day_candidates,
)
from .placement_rules import (
    PlacementRuleResult,
    evaluate_placement_rules,
)
from .session_placement import (
    SessionPlacementContext,
)


@dataclass(frozen=True)
class SessionPlacementCandidate:
    """Évaluation d'un jour candidat pour une séance donnée."""

    date: date

    calendar_score: int
    placement_score: int

    eligible: bool

    preferred: bool
    requires_confirmation: bool

    running_allowed: bool
    cross_training_allowed: bool
    max_duration_minutes: int | None

    rules: tuple[PlacementRuleResult, ...]
    reasons: tuple[str, ...]


def rank_session_placement_candidates(
    *,
    context: SessionPlacementContext,
) -> tuple[SessionPlacementCandidate, ...]:
    """Classe les jours candidats selon calendrier et règles métier."""

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
                not candidate.eligible,
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
    rules = evaluate_placement_rules(
        context=context,
        candidate=candidate,
    )

    hard_violations = tuple(
        rule
        for rule in rules
        if (
            rule.violated
            and rule.severity == "hard"
        )
    )

    soft_adjustment = sum(
        rule.score_adjustment
        for rule in rules
        if (
            rule.violated
            and rule.severity == "soft"
        )
    )

    placement_score = (
        candidate.score
        + soft_adjustment
    )

    reasons = list(
        candidate.reasons
    )

    reasons.extend(
        rule.reason
        for rule in rules
        if rule.violated
    )

    return SessionPlacementCandidate(
        date=candidate.date,
        calendar_score=candidate.score,
        placement_score=placement_score,
        eligible=not hard_violations,
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
        rules=rules,
        reasons=tuple(reasons),
    )
