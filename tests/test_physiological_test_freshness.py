from datetime import date, timedelta

import pytest

from opencoach.physiology.testing import (
    MeasurementConfidence,
    MeasurementFreshness,
    PhysiologicalMeasurementEvidence,
    PhysiologicalMetric,
    PhysiologicalTestAcquisitionMode,
    evaluate_measurement_freshness,
)


TODAY = date(
    2026,
    8,
    28,
)


def measurement(
    metric: PhysiologicalMetric,
    *,
    age_days: int,
) -> PhysiologicalMeasurementEvidence:
    return PhysiologicalMeasurementEvidence(
        metric=metric,
        measured_at=(
            TODAY
            - timedelta(days=age_days)
        ),
        confidence=(
            MeasurementConfidence.HIGH
        ),
        acquisition_mode=(
            PhysiologicalTestAcquisitionMode.SCHEDULED
        ),
    )


def test_missing_measurement_is_missing() -> None:
    result = evaluate_measurement_freshness(
        metric=PhysiologicalMetric.VMA,
        reference_date=TODAY,
        measurement=None,
    )

    assert (
        result
        is MeasurementFreshness.MISSING
    )


def test_recent_vma_is_fresh() -> None:
    result = evaluate_measurement_freshness(
        metric=PhysiologicalMetric.VMA,
        reference_date=TODAY,
        measurement=measurement(
            PhysiologicalMetric.VMA,
            age_days=30,
        ),
    )

    assert (
        result
        is MeasurementFreshness.FRESH
    )


def test_vma_at_70_days_is_aging() -> None:
    result = evaluate_measurement_freshness(
        metric=PhysiologicalMetric.VMA,
        reference_date=TODAY,
        measurement=measurement(
            PhysiologicalMetric.VMA,
            age_days=70,
        ),
    )

    assert (
        result
        is MeasurementFreshness.AGING
    )


def test_vma_at_100_days_is_stale() -> None:
    result = evaluate_measurement_freshness(
        metric=PhysiologicalMetric.VMA,
        reference_date=TODAY,
        measurement=measurement(
            PhysiologicalMetric.VMA,
            age_days=100,
        ),
    )

    assert (
        result
        is MeasurementFreshness.STALE
    )


def test_max_hr_has_longer_freshness_window() -> None:
    result = evaluate_measurement_freshness(
        metric=(
            PhysiologicalMetric.MAX_HEART_RATE
        ),
        reference_date=TODAY,
        measurement=measurement(
            PhysiologicalMetric.MAX_HEART_RATE,
            age_days=100,
        ),
    )

    assert (
        result
        is MeasurementFreshness.FRESH
    )


def test_future_measurement_is_rejected() -> None:
    future = PhysiologicalMeasurementEvidence(
        metric=PhysiologicalMetric.VMA,
        measured_at=(
            TODAY
            + timedelta(days=1)
        ),
        confidence=(
            MeasurementConfidence.HIGH
        ),
        acquisition_mode=(
            PhysiologicalTestAcquisitionMode.MANUAL
        ),
    )

    with pytest.raises(
        ValueError
    ):
        evaluate_measurement_freshness(
            metric=PhysiologicalMetric.VMA,
            reference_date=TODAY,
            measurement=future,
        )
