from datetime import date
from uuid import uuid4

import pytest

from opencoach.models import (
    PhysiologicalMeasurement,
)


def test_creates_vma_measurement() -> None:
    measurement = PhysiologicalMeasurement(
        id=uuid4(),
        metric="vma",
        value=15.6,
        measured_at=date(
            2026,
            9,
            12,
        ),
        protocol="vameval",
        source="field_test",
        confidence="high",
    )

    assert measurement.metric == "vma"
    assert measurement.value == 15.6
    assert measurement.protocol == "vameval"
    assert measurement.source == "field_test"
    assert measurement.confidence == "high"


def test_normalizes_protocol() -> None:
    measurement = PhysiologicalMeasurement(
        id=uuid4(),
        metric="vma",
        value=15.0,
        measured_at=date(
            2026,
            9,
            12,
        ),
        protocol=" VAMEVAL ",
    )

    assert measurement.protocol == "vameval"


def test_allows_measurement_without_protocol() -> None:
    measurement = PhysiologicalMeasurement(
        id=uuid4(),
        metric="resting_heart_rate",
        value=48.0,
        measured_at=date(
            2026,
            9,
            12,
        ),
        source="device",
    )

    assert measurement.protocol is None


def test_rejects_non_positive_value() -> None:
    with pytest.raises(
        ValueError,
        match="strictement positive",
    ):
        PhysiologicalMeasurement(
            id=uuid4(),
            metric="vma",
            value=0,
            measured_at=date(
                2026,
                9,
                12,
            ),
        )


def test_rejects_empty_protocol() -> None:
    with pytest.raises(
        ValueError,
        match="protocole",
    ):
        PhysiologicalMeasurement(
            id=uuid4(),
            metric="vma",
            value=15.0,
            measured_at=date(
                2026,
                9,
                12,
            ),
            protocol="   ",
        )


def test_measurement_is_frozen() -> None:
    measurement = PhysiologicalMeasurement(
        id=uuid4(),
        metric="max_heart_rate",
        value=190.0,
        measured_at=date(
            2026,
            9,
            12,
        ),
    )

    with pytest.raises(
        AttributeError,
    ):
        measurement.value = 195.0
