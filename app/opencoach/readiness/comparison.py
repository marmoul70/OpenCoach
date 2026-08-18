from dataclasses import dataclass

from opencoach.models import WellnessDay

from .models import ReadinessBaseline


@dataclass(frozen=True)
class MetricComparison:
    """Comparaison d'une métrique du jour avec sa baseline."""

    current: float | None
    baseline: float | None

    absolute_delta: float | None
    percent_delta: float | None

    reliable: bool


@dataclass(frozen=True)
class ReadinessComparison:
    """Écarts physiologiques entre aujourd'hui et la baseline."""

    hrv: MetricComparison
    resting_hr: MetricComparison
    sleep_seconds: MetricComparison
    sleep_score: MetricComparison


def compare_with_baseline(
    current: WellnessDay,
    baseline: ReadinessBaseline,
) -> ReadinessComparison:
    """Compare les métriques du jour aux baselines personnelles."""

    return ReadinessComparison(
        hrv=_compare_metric(
            current=(
                float(current.hrv)
                if current.hrv is not None
                else None
            ),
            baseline=baseline.hrv.median,
            reliable=baseline.hrv.reliable,
        ),
        resting_hr=_compare_metric(
            current=(
                float(current.resting_hr)
                if current.resting_hr is not None
                else None
            ),
            baseline=baseline.resting_hr.median,
            reliable=baseline.resting_hr.reliable,
        ),
        sleep_seconds=_compare_metric(
            current=(
                float(current.sleep_seconds)
                if current.sleep_seconds is not None
                else None
            ),
            baseline=baseline.sleep_seconds.median,
            reliable=baseline.sleep_seconds.reliable,
        ),
        sleep_score=_compare_metric(
            current=(
                float(current.sleep_score)
                if current.sleep_score is not None
                else None
            ),
            baseline=baseline.sleep_score.median,
            reliable=baseline.sleep_score.reliable,
        ),
    )


def _compare_metric(
    *,
    current: float | None,
    baseline: float | None,
    reliable: bool,
) -> MetricComparison:
    if (
        current is None
        or baseline is None
        or baseline == 0
    ):
        return MetricComparison(
            current=current,
            baseline=baseline,
            absolute_delta=None,
            percent_delta=None,
            reliable=False,
        )

    absolute_delta = (
        current - baseline
    )

    percent_delta = (
        absolute_delta
        / baseline
        * 100
    )

    return MetricComparison(
        current=current,
        baseline=baseline,
        absolute_delta=round(
            absolute_delta,
            2,
        ),
        percent_delta=round(
            percent_delta,
            1,
        ),
        reliable=reliable,
    )
