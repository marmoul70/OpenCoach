from datetime import date

from opencoach.config import (
    load_threshold_settings,
)
from opencoach.models import DailyContext
from opencoach.readiness import (
    DailyReadiness,
    apply_daily_context,
)


def create_readiness(
    *,
    score: float = 100.0,
    level: str = "high",
) -> DailyReadiness:
    return DailyReadiness(
        score=score,
        level=level,
        signals=(),
        warning_count=0,
        critical_count=0,
        training_constraints=(),
        fitness_ctl=40.0,
        fatigue_atl=35.0,
        training_balance=5.0,
    )


def create_context(
    *,
    fatigue_subjective: int = 1,
    pain_level: int = 0,
    illness_status: str = "none",
    treatment_impact: str = "none",
    motivation: int = 3,
) -> DailyContext:
    return DailyContext(
        date=date(
            2026,
            8,
            18,
        ),
        fatigue_subjective=fatigue_subjective,
        pain_level=pain_level,
        illness_status=illness_status,
        treatment_impact=treatment_impact,
        motivation=motivation,
    )


def calculate(
    context: DailyContext | None,
):
    thresholds = (
        load_threshold_settings()
        .readiness
    )

    return apply_daily_context(
        readiness=create_readiness(),
        context=context,
        thresholds=thresholds,
    )


def get_signal(
    result: DailyReadiness,
    metric: str,
):
    return next(
        signal
        for signal in result.signals
        if signal.metric == metric
    )


def test_no_context_keeps_readiness_unchanged() -> None:
    readiness = create_readiness()

    thresholds = (
        load_threshold_settings()
        .readiness
    )

    result = apply_daily_context(
        readiness=readiness,
        context=None,
        thresholds=thresholds,
    )

    assert result == readiness


def test_normal_context_keeps_high_readiness() -> None:
    result = calculate(
        create_context()
    )

    assert result.score == 100.0
    assert result.level == "high"
    assert result.warning_count == 0
    assert result.critical_count == 0


def test_high_subjective_fatigue_adds_warning() -> None:
    result = calculate(
        create_context(
            fatigue_subjective=4,
        )
    )

    signal = get_signal(
        result,
        "subjective_fatigue",
    )

    assert signal.level == "warning"
    assert result.score == 90.0
    assert result.warning_count == 1


def test_critical_subjective_fatigue_adds_critical() -> None:
    result = calculate(
        create_context(
            fatigue_subjective=5,
        )
    )

    signal = get_signal(
        result,
        "subjective_fatigue",
    )

    assert signal.level == "critical"
    assert result.score == 75.0
    assert result.critical_count == 1

    assert (
        "reduce_duration"
        in result.training_constraints
    )


def test_significant_treatment_caps_readiness() -> None:
    result = calculate(
        create_context(
            treatment_impact="significant",
        )
    )

    signal = get_signal(
        result,
        "treatment_impact",
    )

    assert signal.level == "critical"

    assert result.score == 50.0
    assert result.level == "moderate"

    assert (
        "prefer_recovery_or_rest"
        in result.training_constraints
    )

    assert (
        "avoid_high_intensity"
        in result.training_constraints
    )


def test_significant_illness_caps_readiness() -> None:
    result = calculate(
        create_context(
            illness_status="significant",
        )
    )

    signal = get_signal(
        result,
        "illness",
    )

    assert signal.level == "critical"

    assert result.score == 29.0
    assert result.level == "very_low"

    assert (
        "prefer_recovery_or_rest"
        in result.training_constraints
    )


def test_critical_pain_caps_readiness() -> None:
    result = calculate(
        create_context(
            pain_level=8,
        )
    )

    signal = get_signal(
        result,
        "pain",
    )

    assert signal.level == "critical"

    assert result.score == 40.0
    assert result.level == "low"

    assert (
        "avoid_pain_aggravation"
        in result.training_constraints
    )


def test_multiple_context_issues_accumulate() -> None:
    result = calculate(
        create_context(
            fatigue_subjective=5,
            pain_level=8,
            treatment_impact="significant",
        )
    )

    assert result.critical_count == 3

    # 100 - 3 × 25 = 25.
    # Les caps ne peuvent pas remonter le score.
    assert result.score == 25.0
    assert result.level == "very_low"


def test_low_motivation_adds_constraint_without_penalty() -> None:
    result = calculate(
        create_context(
            motivation=1,
        )
    )

    assert result.score == 100.0

    assert (
        "consider_low_motivation"
        in result.training_constraints
    )
