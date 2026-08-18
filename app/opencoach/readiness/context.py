from dataclasses import replace

from opencoach.config import (
    ReadinessContextThresholds,
    ReadinessThresholds,
)
from opencoach.models import DailyContext

from .models import (
    DailyReadiness,
    ReadinessLevel,
    ReadinessSignal,
)


def apply_daily_context(
    *,
    readiness: DailyReadiness,
    context: DailyContext | None,
    thresholds: ReadinessThresholds,
) -> DailyReadiness:
    """Applique le contexte subjectif au Daily Readiness.

    Le score physiologique est conservé comme point de départ.
    Le contexte peut ajouter des pénalités, des signaux,
    des contraintes et des plafonds de score.
    """

    if context is None:
        return readiness

    context_thresholds = (
        thresholds.context
    )

    context_signals = [
        _evaluate_fatigue(
            context,
            context_thresholds,
        ),
        _evaluate_pain(
            context,
            context_thresholds,
        ),
        _evaluate_illness(
            context,
            context_thresholds,
        ),
        _evaluate_treatment(
            context,
            context_thresholds,
        ),
    ]

    warning_count = (
        readiness.warning_count
        + sum(
            signal.level == "warning"
            for signal in context_signals
        )
    )

    critical_count = (
        readiness.critical_count
        + sum(
            signal.level == "critical"
            for signal in context_signals
        )
    )

    score = readiness.score

    context_warning_count = sum(
        signal.level == "warning"
        for signal in context_signals
    )

    context_critical_count = sum(
        signal.level == "critical"
        for signal in context_signals
    )

    score -= (
        context_warning_count
        * thresholds.penalties.warning
    )

    score -= (
        context_critical_count
        * thresholds.penalties.critical
    )

    score = max(
        0.0,
        min(
            100.0,
            score,
        ),
    )

    score = _apply_context_caps(
        score=score,
        context=context,
        thresholds=context_thresholds,
    )

    score = round(
        score,
        1,
    )

    level = _score_to_level(
        score,
        thresholds,
    )

    constraints = list(
        readiness.training_constraints
    )

    _append_context_constraints(
        constraints=constraints,
        context=context,
        context_signals=context_signals,
        thresholds=context_thresholds,
    )

    return replace(
        readiness,
        score=score,
        level=level,
        signals=(
            readiness.signals
            + tuple(context_signals)
        ),
        warning_count=warning_count,
        critical_count=critical_count,
        training_constraints=tuple(
            constraints
        ),
    )


def _evaluate_fatigue(
    context: DailyContext,
    thresholds: ReadinessContextThresholds,
) -> ReadinessSignal:
    value = context.fatigue_subjective

    if (
        value
        >= thresholds.fatigue.critical_min
    ):
        level = "critical"

    elif (
        value
        >= thresholds.fatigue.warning_min
    ):
        level = "warning"

    else:
        level = "normal"

    return ReadinessSignal(
        metric="subjective_fatigue",
        level=level,
        reason=(
            f"Fatigue subjective : {value}/5."
        ),
        current_value=float(value),
    )


def _evaluate_pain(
    context: DailyContext,
    thresholds: ReadinessContextThresholds,
) -> ReadinessSignal:
    value = context.pain_level

    if (
        value
        >= thresholds.pain.critical_min
    ):
        level = "critical"

    elif (
        value
        >= thresholds.pain.warning_min
    ):
        level = "warning"

    else:
        level = "normal"

    return ReadinessSignal(
        metric="pain",
        level=level,
        reason=(
            f"Douleur subjective : {value}/10."
        ),
        current_value=float(value),
    )


def _evaluate_illness(
    context: DailyContext,
    thresholds: ReadinessContextThresholds,
) -> ReadinessSignal:
    if context.illness_status == "significant":
        level = (
            thresholds
            .illness
            .significant_level
        )

    elif context.illness_status == "mild":
        level = (
            thresholds
            .illness
            .mild_level
        )

    else:
        level = "normal"

    return ReadinessSignal(
        metric="illness",
        level=level,
        reason=(
            "État de santé subjectif : "
            f"{context.illness_status}."
        ),
    )


def _evaluate_treatment(
    context: DailyContext,
    thresholds: ReadinessContextThresholds,
) -> ReadinessSignal:
    if (
        context.treatment_impact
        == "significant"
    ):
        level = (
            thresholds
            .treatment
            .significant_level
        )

    elif (
        context.treatment_impact
        == "mild"
    ):
        level = (
            thresholds
            .treatment
            .mild_level
        )

    else:
        level = "normal"

    return ReadinessSignal(
        metric="treatment_impact",
        level=level,
        reason=(
            "Impact ressenti du traitement : "
            f"{context.treatment_impact}."
        ),
    )


def _apply_context_caps(
    *,
    score: float,
    context: DailyContext,
    thresholds: ReadinessContextThresholds,
) -> float:
    if (
        context.treatment_impact
        == "significant"
    ):
        score = min(
            score,
            thresholds.caps.significant_treatment,
        )

    if (
        context.illness_status
        == "significant"
    ):
        score = min(
            score,
            thresholds.caps.significant_illness,
        )

    if (
        context.pain_level
        >= thresholds.pain.critical_min
    ):
        score = min(
            score,
            thresholds.caps.critical_pain,
        )

    return score


def _append_context_constraints(
    *,
    constraints: list[str],
    context: DailyContext,
    context_signals: list[ReadinessSignal],
    thresholds: ReadinessContextThresholds,
) -> None:
    critical_metrics = {
        signal.metric
        for signal in context_signals
        if signal.level == "critical"
    }

    if (
        "subjective_fatigue"
        in critical_metrics
    ):
        _append_unique(
            constraints,
            "reduce_duration",
        )

    if "pain" in critical_metrics:
        _append_unique(
            constraints,
            "avoid_high_intensity",
        )

        _append_unique(
            constraints,
            "avoid_pain_aggravation",
        )

    if "illness" in critical_metrics:
        _append_unique(
            constraints,
            "prefer_recovery_or_rest",
        )

    if (
        "treatment_impact"
        in critical_metrics
    ):
        _append_unique(
            constraints,
            "prefer_recovery_or_rest",
        )

        _append_unique(
            constraints,
            "avoid_high_intensity",
        )

    if (
        context.motivation
        <= thresholds.motivation.low_max
    ):
        _append_unique(
            constraints,
            "consider_low_motivation",
        )


def _score_to_level(
    score: float,
    thresholds: ReadinessThresholds,
) -> ReadinessLevel:
    if score >= thresholds.score.high_min:
        return "high"

    if score >= thresholds.score.good_min:
        return "good"

    if score >= thresholds.score.moderate_min:
        return "moderate"

    if score >= thresholds.score.low_min:
        return "low"

    return "very_low"


def _append_unique(
    values: list[str],
    value: str,
) -> None:
    if value not in values:
        values.append(value)
