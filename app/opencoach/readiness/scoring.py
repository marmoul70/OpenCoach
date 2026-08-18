from opencoach.config import ReadinessThresholds
from opencoach.models import WellnessDay

from .comparison import ReadinessComparison
from .models import (
    DailyReadiness,
    ReadinessLevel,
    ReadinessSignal,
)


def calculate_daily_readiness(
    *,
    current: WellnessDay,
    comparison: ReadinessComparison,
    thresholds: ReadinessThresholds,
) -> DailyReadiness:
    """Calcule l'état de disponibilité quotidien."""

    signals = [
        _evaluate_hrv(
            comparison,
            thresholds,
        ),
        _evaluate_resting_hr(
            comparison,
            thresholds,
        ),
        _evaluate_sleep_duration(
            comparison,
            thresholds,
        ),
        _evaluate_sleep_score(
            comparison,
            thresholds,
        ),
        _evaluate_training_load(
            current,
            thresholds,
        ),
    ]

    warning_count = sum(
        signal.level == "warning"
        for signal in signals
    )

    critical_count = sum(
        signal.level == "critical"
        for signal in signals
    )

    score = 100.0

    score -= (
        warning_count
        * thresholds.penalties.warning
    )

    score -= (
        critical_count
        * thresholds.penalties.critical
    )

    score = max(
        0.0,
        min(
            100.0,
            score,
        ),
    )

    if critical_count >= 2:
        score = min(
            score,
            thresholds.score.multiple_critical_cap,
        )

    elif critical_count == 1:
        score = min(
            score,
            thresholds.score.single_critical_cap,
        )

    score = round(
        score,
        1,
    )

    level = _score_to_level(
        score,
        thresholds,
    )

    constraints = _build_training_constraints(
        level=level,
        signals=signals,
    )

    training_balance = None

    if (
        current.fitness_ctl is not None
        and current.fatigue_atl is not None
    ):
        training_balance = round(
            current.fitness_ctl
            - current.fatigue_atl,
            2,
        )

    return DailyReadiness(
        score=score,
        level=level,
        signals=tuple(signals),
        warning_count=warning_count,
        critical_count=critical_count,
        training_constraints=tuple(
            constraints
        ),
        fitness_ctl=current.fitness_ctl,
        fatigue_atl=current.fatigue_atl,
        training_balance=training_balance,
    )


def _evaluate_hrv(
    comparison: ReadinessComparison,
    thresholds: ReadinessThresholds,
) -> ReadinessSignal:
    metric = comparison.hrv

    if (
        not metric.reliable
        or metric.percent_delta is None
    ):
        return ReadinessSignal(
            metric="hrv",
            level="unavailable",
            reason=(
                "Baseline HRV insuffisante "
                "ou mesure indisponible."
            ),
            current_value=metric.current,
            reference_value=metric.baseline,
        )

    if (
        metric.percent_delta
        <= thresholds.hrv.critical_percent
    ):
        level = "critical"

    elif (
        metric.percent_delta
        <= thresholds.hrv.warning_percent
    ):
        level = "warning"

    else:
        level = "normal"

    return ReadinessSignal(
        metric="hrv",
        level=level,
        reason=(
            f"HRV {metric.percent_delta:+.1f} % "
            "par rapport à la baseline."
        ),
        current_value=metric.current,
        reference_value=metric.baseline,
    )


def _evaluate_resting_hr(
    comparison: ReadinessComparison,
    thresholds: ReadinessThresholds,
) -> ReadinessSignal:
    metric = comparison.resting_hr

    if (
        not metric.reliable
        or metric.percent_delta is None
    ):
        return ReadinessSignal(
            metric="resting_hr",
            level="unavailable",
            reason=(
                "Baseline FC repos insuffisante "
                "ou mesure indisponible."
            ),
            current_value=metric.current,
            reference_value=metric.baseline,
        )

    if (
        metric.percent_delta
        >= thresholds.resting_hr.critical_percent
    ):
        level = "critical"

    elif (
        metric.percent_delta
        >= thresholds.resting_hr.warning_percent
    ):
        level = "warning"

    else:
        level = "normal"

    return ReadinessSignal(
        metric="resting_hr",
        level=level,
        reason=(
            f"FC repos {metric.percent_delta:+.1f} % "
            "par rapport à la baseline."
        ),
        current_value=metric.current,
        reference_value=metric.baseline,
    )


def _evaluate_sleep_duration(
    comparison: ReadinessComparison,
    thresholds: ReadinessThresholds,
) -> ReadinessSignal:
    metric = comparison.sleep_seconds

    if metric.current is None:
        return ReadinessSignal(
            metric="sleep_duration",
            level="unavailable",
            reason="Durée de sommeil indisponible.",
        )

    current_hours = (
        metric.current
        / 3600
    )

    critical = (
        current_hours
        <= thresholds.sleep_duration.critical_hours
    )

    warning = (
        current_hours
        <= thresholds.sleep_duration.warning_hours
    )

    if (
        metric.reliable
        and metric.percent_delta is not None
    ):
        critical = (
            critical
            or metric.percent_delta
            <= thresholds.sleep_duration.critical_percent
        )

        warning = (
            warning
            or metric.percent_delta
            <= thresholds.sleep_duration.warning_percent
        )

    if critical:
        level = "critical"

    elif warning:
        level = "warning"

    else:
        level = "normal"

    return ReadinessSignal(
        metric="sleep_duration",
        level=level,
        reason=(
            f"Sommeil {current_hours:.1f} h"
            + (
                (
                    f", {metric.percent_delta:+.1f} % "
                    "vs baseline."
                )
                if metric.percent_delta is not None
                else "."
            )
        ),
        current_value=metric.current,
        reference_value=metric.baseline,
    )


def _evaluate_sleep_score(
    comparison: ReadinessComparison,
    thresholds: ReadinessThresholds,
) -> ReadinessSignal:
    metric = comparison.sleep_score

    if metric.current is None:
        return ReadinessSignal(
            metric="sleep_score",
            level="unavailable",
            reason="Score de sommeil indisponible.",
        )

    if (
        metric.current
        <= thresholds.sleep_score.critical_value
    ):
        level = "critical"

    elif (
        metric.current
        <= thresholds.sleep_score.warning_value
    ):
        level = "warning"

    else:
        level = "normal"

    return ReadinessSignal(
        metric="sleep_score",
        level=level,
        reason=(
            f"Score de sommeil : "
            f"{metric.current:.0f}."
        ),
        current_value=metric.current,
        reference_value=metric.baseline,
    )


def _evaluate_training_load(
    current: WellnessDay,
    thresholds: ReadinessThresholds,
) -> ReadinessSignal:
    if (
        current.fitness_ctl is None
        or current.fatigue_atl is None
    ):
        return ReadinessSignal(
            metric="training_load",
            level="unavailable",
            reason=(
                "CTL ou ATL indisponible."
            ),
        )

    balance = (
        current.fitness_ctl
        - current.fatigue_atl
    )

    if (
        balance
        <= thresholds.training_load.critical_balance
    ):
        level = "critical"

    elif (
        balance
        <= thresholds.training_load.warning_balance
    ):
        level = "warning"

    else:
        level = "normal"

    return ReadinessSignal(
        metric="training_load",
        level=level,
        reason=(
            f"Balance de charge CTL-ATL : "
            f"{balance:+.1f}."
        ),
        current_value=round(
            balance,
            2,
        ),
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


def _build_training_constraints(
    *,
    level: ReadinessLevel,
    signals: list[ReadinessSignal],
) -> list[str]:
    constraints: list[str] = []

    if level == "moderate":
        constraints.append(
            "monitor_intensity"
        )

    elif level == "low":
        constraints.extend(
            [
                "avoid_high_intensity",
                "reduce_duration",
            ]
        )

    elif level == "very_low":
        constraints.extend(
            [
                "avoid_high_intensity",
                "reduce_duration",
                "prefer_recovery_or_rest",
            ]
        )

    critical_metrics = {
        signal.metric
        for signal in signals
        if signal.level == "critical"
    }

    if (
        "sleep_duration"
        in critical_metrics
    ):
        _append_unique(
            constraints,
            "avoid_high_intensity",
        )

    if "hrv" in critical_metrics:
        _append_unique(
            constraints,
            "monitor_recovery",
        )

    if (
        "training_load"
        in critical_metrics
    ):
        _append_unique(
            constraints,
            "reduce_training_load",
        )

    return constraints


def _append_unique(
    values: list[str],
    value: str,
) -> None:
    if value not in values:
        values.append(value)
