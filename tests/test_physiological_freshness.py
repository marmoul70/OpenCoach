from datetime import date, timedelta
from uuid import uuid4

import pytest

from opencoach.models import (
    PhysiologicalMeasurement,
)
from opencoach.planning import (
    assess_measurement_freshness,
)


REFERENCE_DATE = date(
    2026,
    8,
    22,
)


def create_measurement(
    *,
    metric: str,
    age_days: int,
    confidence: str = "high",
) -> PhysiologicalMeasurement:
    return PhysiologicalMeasurement(
        id=uuid4(),
        metric=metric,
        value=15.0,
        measured_at=(
            REFERENCE_DATE
            - timedelta(days=age_days)
        ),
        protocol="test",
        source="field_test",
        confidence=confidence,
    )


def test_recent_vma_is_fresh() -> None:
    assessment = assess_measurement_freshness(
        measurement=create_measurement(
            metric="vma",
            age_days=45,
        ),
        reference_date=REFERENCE_DATE,
    )

    assert assessment.freshness == "fresh"
    assert assessment.usable is True

    assert (
        assessment.recalibration_recommended
        is False
    )


def test_aging_vma_remains_usable() -> None:
    assessment = assess_measurement_freshness(
        measurement=create_measurement(
            metric="vma",
            age_days=120,
        ),
        reference_date=REFERENCE_DATE,
    )

    assert assessment.freshness == "aging"
    assert assessment.usable is True

    assert (
        assessment.recalibration_recommended
        is False
    )


def test_stale_vma_requires_recalibration() -> None:
    assessment = assess_measurement_freshness(
        measurement=create_measurement(
            metric="vma",
            age_days=220,
        ),
        reference_date=REFERENCE_DATE,
    )

    assert assessment.freshness == "stale"
    assert assessment.usable is False

    assert (
        assessment.recalibration_recommended
        is True
    )


def test_max_heart_rate_ages_more_slowly() -> None:
    assessment = assess_measurement_freshness(
        measurement=create_measurement(
            metric="max_heart_rate",
            age_days=150,
        ),
        reference_date=REFERENCE_DATE,
    )

    assert assessment.freshness == "fresh"
    assert assessment.usable is True


def test_resting_heart_rate_ages_quickly() -> None:
    assessment = assess_measurement_freshness(
        measurement=create_measurement(
            metric="resting_heart_rate",
            age_days=45,
        ),
        reference_date=REFERENCE_DATE,
    )

    assert assessment.freshness == "aging"


def test_low_confidence_measurement_is_not_usable() -> None:
    assessment = assess_measurement_freshness(
        measurement=create_measurement(
            metric="vma",
            age_days=20,
            confidence="low",
        ),
        reference_date=REFERENCE_DATE,
    )

    assert assessment.freshness == "fresh"
    assert assessment.usable is False

    assert (
        assessment.recalibration_recommended
        is True
    )


def test_future_measurement_is_rejected() -> None:
    measurement = PhysiologicalMeasurement(
        id=uuid4(),
        metric="vma",
        value=15.0,
        measured_at=(
            REFERENCE_DATE
            + timedelta(days=1)
        ),
        source="field_test",
        confidence="high",
    )

    with pytest.raises(
        ValueError,
        match="postérieure",
    ):
        assess_measurement_freshness(
            measurement=measurement,
            reference_date=REFERENCE_DATE,
        )
