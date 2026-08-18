from datetime import date

from opencoach.config import (
    load_threshold_settings,
)
from opencoach.models import WellnessDay
from opencoach.readiness import (
    MetricComparison,
    ReadinessComparison,
    calculate_daily_readiness,
)


CURRENT_DATE = date(
    2026,
    8,
    18,
)


def make_metric(
    *,
    current: float | None,
    baseline: float | None,
    percent_delta: float | None = 0.0,
    reliable: bool = True,
) -> MetricComparison:
    """Construit une comparaison de métrique pour les tests."""

    absolute_delta = None

    if (
        current is not None
        and baseline is not None
    ):
        absolute_delta = (
            current - baseline
        )

    return MetricComparison(
        current=current,
        baseline=baseline,
        absolute_delta=absolute_delta,
        percent_delta=percent_delta,
        reliable=reliable,
    )


def make_comparison(
    *,
    hrv_percent: float | None = 0.0,
    resting_hr_percent: float | None = 0.0,
    sleep_percent: float | None = 0.0,
    hrv_current: float | None = 52.0,
    resting_hr_current: float | None = 46.0,
    sleep_seconds: float | None = 27000.0,
    sleep_score: float | None = 82.0,
    hrv_reliable: bool = True,
    resting_hr_reliable: bool = True,
    sleep_reliable: bool = True,
) -> ReadinessComparison:
    """Construit une comparaison Readiness standard."""

    return ReadinessComparison(
        hrv=make_metric(
            current=hrv_current,
            baseline=52.0,
            percent_delta=hrv_percent,
            reliable=hrv_reliable,
        ),
        resting_hr=make_metric(
            current=resting_hr_current,
            baseline=46.0,
            percent_delta=resting_hr_percent,
            reliable=resting_hr_reliable,
        ),
        sleep_seconds=make_metric(
            current=sleep_seconds,
            baseline=27000.0,
            percent_delta=sleep_percent,
            reliable=sleep_reliable,
        ),
        sleep_score=make_metric(
            current=sleep_score,
            baseline=80.0,
            percent_delta=(
                (
                    (
                        sleep_score
                        - 80.0
                    )
                    / 80.0
                    * 100.0
                )
                if sleep_score is not None
                else None
            ),
            reliable=True,
        ),
    )


def make_wellness(
    *,
    fitness_ctl: float | None = 40.0,
    fatigue_atl: float | None = 35.0,
    hrv: float | None = 52.0,
    resting_hr: int | None = 46,
    sleep_seconds: int | None = 27000,
    sleep_score: float | None = 82.0,
) -> WellnessDay:
    """Construit une journée Wellness standard."""

    return WellnessDay(
        provider="intervals",
        date=CURRENT_DATE,
        fitness_ctl=fitness_ctl,
        fatigue_atl=fatigue_atl,
        hrv=hrv,
        resting_hr=resting_hr,
        sleep_seconds=sleep_seconds,
        sleep_score=sleep_score,
    )


def get_signal(
    result,
    metric: str,
):
    """Retourne un signal Readiness par son nom."""

    return next(
        signal
        for signal in result.signals
        if signal.metric == metric
    )


def calculate(
    *,
    current: WellnessDay | None = None,
    comparison: ReadinessComparison | None = None,
):
    """Calcule un Readiness avec la configuration projet."""

    thresholds = (
        load_threshold_settings()
        .readiness
    )

    return calculate_daily_readiness(
        current=(
            current
            if current is not None
            else make_wellness()
        ),
        comparison=(
            comparison
            if comparison is not None
            else make_comparison()
        ),
        thresholds=thresholds,
    )


def test_good_recovery_produces_high_readiness() -> None:
    result = calculate()

    assert result.score == 100.0
    assert result.level == "high"

    assert result.warning_count == 0
    assert result.critical_count == 0

    assert result.training_balance == 5.0
    assert result.training_constraints == ()


def test_low_hrv_produces_warning() -> None:
    result = calculate(
        comparison=make_comparison(
            hrv_percent=-15.0,
            hrv_current=44.2,
        ),
    )

    signal = get_signal(
        result,
        "hrv",
    )

    assert signal.level == "warning"

    assert result.score == 90.0
    assert result.level == "high"

    assert result.warning_count == 1
    assert result.critical_count == 0


def test_very_low_hrv_produces_critical_signal() -> None:
    result = calculate(
        comparison=make_comparison(
            hrv_percent=-25.0,
            hrv_current=39.0,
        ),
    )

    signal = get_signal(
        result,
        "hrv",
    )

    assert signal.level == "critical"

    assert result.score == 60.0
    assert result.level == "moderate"

    assert result.warning_count == 0
    assert result.critical_count == 1

    assert (
        "monitor_recovery"
        in result.training_constraints
    )


def test_high_resting_hr_produces_warning() -> None:
    result = calculate(
        comparison=make_comparison(
            resting_hr_percent=9.0,
            resting_hr_current=50.1,
        ),
    )

    signal = get_signal(
        result,
        "resting_hr",
    )

    assert signal.level == "warning"

    assert result.score == 90.0
    assert result.warning_count == 1
    assert result.critical_count == 0


def test_short_sleep_produces_warning() -> None:
    sleep_seconds = int(
        5.5
        * 3600
    )

    result = calculate(
        current=make_wellness(
            sleep_seconds=sleep_seconds,
        ),
        comparison=make_comparison(
            sleep_seconds=float(
                sleep_seconds
            ),
            sleep_percent=-10.0,
        ),
    )

    signal = get_signal(
        result,
        "sleep_duration",
    )

    assert signal.level == "warning"

    assert result.score == 90.0
    assert result.warning_count == 1


def test_very_short_sleep_produces_critical_signal() -> None:
    sleep_seconds = int(
        4.0
        * 3600
    )

    result = calculate(
        current=make_wellness(
            sleep_seconds=sleep_seconds,
        ),
        comparison=make_comparison(
            sleep_seconds=float(
                sleep_seconds
            ),
            sleep_percent=-20.0,
        ),
    )

    signal = get_signal(
        result,
        "sleep_duration",
    )

    assert signal.level == "critical"

    assert result.score == 60.0
    assert result.level == "moderate"

    assert (
        "avoid_high_intensity"
        in result.training_constraints
    )


def test_high_training_fatigue_produces_warning() -> None:
    result = calculate(
        current=make_wellness(
            fitness_ctl=40.0,
            fatigue_atl=52.0,
        ),
    )

    signal = get_signal(
        result,
        "training_load",
    )

    assert signal.level == "warning"

    assert result.training_balance == -12.0
    assert result.score == 90.0

    assert result.warning_count == 1
    assert result.critical_count == 0


def test_very_high_training_fatigue_produces_critical() -> None:
    result = calculate(
        current=make_wellness(
            fitness_ctl=40.0,
            fatigue_atl=65.0,
        ),
    )

    signal = get_signal(
        result,
        "training_load",
    )

    assert signal.level == "critical"

    assert result.training_balance == -25.0

    assert result.score == 60.0
    assert result.level == "moderate"

    assert (
        "reduce_training_load"
        in result.training_constraints
    )


def test_two_critical_signals_produce_very_low_readiness() -> None:
    sleep_seconds = int(
        4.0
        * 3600
    )

    result = calculate(
        current=make_wellness(
            sleep_seconds=sleep_seconds,
        ),
        comparison=make_comparison(
            hrv_percent=-25.0,
            hrv_current=39.0,
            sleep_seconds=float(
                sleep_seconds
            ),
            sleep_percent=-20.0,
        ),
    )

    assert result.critical_count == 2

    assert result.score == 29.0
    assert result.level == "very_low"

    assert (
        "avoid_high_intensity"
        in result.training_constraints
    )

    assert (
        "reduce_duration"
        in result.training_constraints
    )

    assert (
        "prefer_recovery_or_rest"
        in result.training_constraints
    )

    assert (
        "monitor_recovery"
        in result.training_constraints
    )


def test_missing_hrv_does_not_penalize_readiness() -> None:
    result = calculate(
        current=make_wellness(
            hrv=None,
        ),
        comparison=make_comparison(
            hrv_current=None,
            hrv_percent=None,
            hrv_reliable=False,
        ),
    )

    signal = get_signal(
        result,
        "hrv",
    )

    assert signal.level == "unavailable"

    assert result.score == 100.0
    assert result.level == "high"

    assert result.warning_count == 0
    assert result.critical_count == 0


def test_missing_training_load_does_not_penalize_readiness() -> None:
    result = calculate(
        current=make_wellness(
            fitness_ctl=None,
            fatigue_atl=None,
        ),
    )

    signal = get_signal(
        result,
        "training_load",
    )

    assert signal.level == "unavailable"

    assert result.training_balance is None

    assert result.score == 100.0
    assert result.level == "high"


def test_low_sleep_score_produces_warning() -> None:
    result = calculate(
        current=make_wellness(
            sleep_score=60.0,
        ),
        comparison=make_comparison(
            sleep_score=60.0,
        ),
    )

    signal = get_signal(
        result,
        "sleep_score",
    )

    assert signal.level == "warning"

    assert result.score == 90.0
    assert result.warning_count == 1


def test_very_low_sleep_score_produces_critical() -> None:
    result = calculate(
        current=make_wellness(
            sleep_score=45.0,
        ),
        comparison=make_comparison(
            sleep_score=45.0,
        ),
    )

    signal = get_signal(
        result,
        "sleep_score",
    )

    assert signal.level == "critical"

    assert result.score == 60.0
    assert result.level == "moderate"