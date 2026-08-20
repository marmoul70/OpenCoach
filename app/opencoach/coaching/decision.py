from opencoach.config import (
    CoachDecisionThresholds,
)
from opencoach.models import TrainingSession
from opencoach.readiness import DailyReadiness

from .models import CoachDecision
from opencoach.training import (
    RecentLoadAssessment,
)

def decide_training_session(
    *,
    session: TrainingSession,
    readiness: DailyReadiness,
    thresholds: CoachDecisionThresholds,
    recent_load: RecentLoadAssessment | None = None,
) -> CoachDecision:
    """Décide comment adapter une séance selon le contexte disponible."""

    score = readiness.score

    if (
        recent_load is not None
        and recent_load.has_critical
    ):
        return _build_recent_load_reduction(
            session=session,
            readiness=readiness,
            thresholds=thresholds,
            recent_load=recent_load,
        )

    if (
        "prefer_recovery_or_rest"
        in readiness.training_constraints
        and score
        < thresholds.readiness.reduce_min
    ):
        return _build_rest_decision(
            session=session,
            readiness=readiness,
        )

    if score >= thresholds.readiness.keep_min:
        return _build_keep_decision(
            session=session,
            readiness=readiness,
        )

    if score >= thresholds.readiness.reduce_min:
        return _build_reduce_decision(
            session=session,
            readiness=readiness,
            thresholds=thresholds,
        )

    if score >= thresholds.readiness.replace_min:
        return _build_replace_decision(
            session=session,
            readiness=readiness,
            thresholds=thresholds,
        )

    return _build_rest_decision(
        session=session,
        readiness=readiness,
    )

def _build_keep_decision(
    *,
    session: TrainingSession,
    readiness: DailyReadiness,
) -> CoachDecision:
    return CoachDecision(
        action="keep",
        reason=(
            "Disponibilité suffisante pour conserver "
            "la séance planifiée."
        ),
        original_duration_minutes=(
            session.duration_minutes
        ),
        recommended_duration_minutes=(
            session.duration_minutes
        ),
        duration_factor=1.0,
        intensity_factor=1.0,
        original_intensity=session.intensity,
        recommended_intensity=session.intensity,
        constraints=(
            readiness.training_constraints
        ),
    )


def _build_reduce_decision(
    *,
    session: TrainingSession,
    readiness: DailyReadiness,
    thresholds: CoachDecisionThresholds,
) -> CoachDecision:
    duration_factor = (
        thresholds
        .reduction
        .duration_factor
    )

    if (
        "avoid_high_intensity"
        in readiness.training_constraints
    ):
        duration_factor *= (
            thresholds
            .constraints
            .avoid_high_intensity_duration_factor
        )

    duration_factor = round(
        duration_factor,
        3,
    )

    recommended_duration = _scaled_duration(
        session.duration_minutes,
        duration_factor,
    )

    recommended_intensity = (
        "easy"
        if (
            "avoid_high_intensity"
            in readiness.training_constraints
        )
        else session.intensity
    )

    return CoachDecision(
        action="reduce",
        reason=(
            "La récupération permet de maintenir "
            "l'entraînement avec une charge réduite."
        ),
        original_duration_minutes=(
            session.duration_minutes
        ),
        recommended_duration_minutes=(
            recommended_duration
        ),
        duration_factor=duration_factor,
        intensity_factor=(
            thresholds
            .reduction
            .intensity_factor
        ),
        original_intensity=session.intensity,
        recommended_intensity=(
            recommended_intensity
        ),
        constraints=(
            readiness.training_constraints
        ),
    )

def _build_recent_load_reduction(
    *,
    session: TrainingSession,
    readiness: DailyReadiness,
    thresholds: CoachDecisionThresholds,
    recent_load: RecentLoadAssessment,
) -> CoachDecision:
    """Réduit la séance lorsqu'une surcharge récente est détectée."""

    duration_factor = (
        thresholds
        .reduction
        .duration_factor
    )

    recommended_duration = _scaled_duration(
        session.duration_minutes,
        duration_factor,
    )

    critical_reasons = [
        signal.reason
        for signal in recent_load.signals
        if signal.level == "critical"
    ]

    reason = (
        critical_reasons[0]
        if critical_reasons
        else (
            "La charge récente justifie une réduction "
            "de la séance planifiée."
        )
    )

    constraints = tuple(
        dict.fromkeys(
            (
                *readiness.training_constraints,
                *(
                    signal.kind
                    for signal in recent_load.signals
                    if signal.level == "critical"
                ),
            )
        )
    )

    return CoachDecision(
        action="reduce",
        reason=reason,
        original_duration_minutes=(
            session.duration_minutes
        ),
        recommended_duration_minutes=(
            recommended_duration
        ),
        duration_factor=duration_factor,
        intensity_factor=(
            thresholds
            .reduction
            .intensity_factor
        ),
        original_intensity=session.intensity,
        recommended_intensity="easy",
        constraints=constraints,
    )

def _build_replace_decision(
    *,
    session: TrainingSession,
    readiness: DailyReadiness,
    thresholds: CoachDecisionThresholds,
) -> CoachDecision:
    recommended_duration = min(
        session.duration_minutes,
        thresholds
        .constraints
        .recovery_max_duration_minutes,
    )

    return CoachDecision(
        action="replace",
        reason=(
            "La disponibilité est insuffisante pour "
            "la séance prévue. Une séance de "
            "récupération est privilégiée."
        ),
        original_duration_minutes=(
            session.duration_minutes
        ),
        recommended_duration_minutes=(
            recommended_duration
        ),
        duration_factor=(
            round(
                recommended_duration
                / session.duration_minutes,
                3,
            )
            if session.duration_minutes > 0
            else None
        ),
        intensity_factor=None,
        original_intensity=session.intensity,
        recommended_intensity="very_easy",
        constraints=(
            readiness.training_constraints
        ),
    )


def _build_rest_decision(
    *,
    session: TrainingSession,
    readiness: DailyReadiness,
) -> CoachDecision:
    return CoachDecision(
        action="rest",
        reason=(
            "La disponibilité est trop faible pour "
            "maintenir une séance d'entraînement."
        ),
        original_duration_minutes=(
            session.duration_minutes
        ),
        recommended_duration_minutes=None,
        duration_factor=None,
        intensity_factor=None,
        original_intensity=session.intensity,
        recommended_intensity=None,
        constraints=(
            readiness.training_constraints
        ),
    )


def _scaled_duration(
    duration_minutes: int,
    factor: float,
) -> int:
    return max(
        1,
        round(
            duration_minutes
            * factor
        ),
    )
