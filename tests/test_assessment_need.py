from datetime import date, timedelta
from uuid import uuid4

from opencoach.models import (
    AthleteProfile,
    PhysiologicalMeasurement,
)
from opencoach.planning import (
    PhysiologicalCalibrationSnapshotService,
    identify_assessment_needs,
)


REFERENCE_DATE = date(
    2026,
    8,
    22,
)


class FakeMeasurementRepository:
    def __init__(
        self,
        measurements=(),
    ) -> None:
        self.measurements = tuple(
            measurements
        )

    def get_latest_measurement(
        self,
        athlete_profile_id,
        metric,
    ):
        matching = [
            measurement
            for measurement in self.measurements
            if measurement.metric == metric
        ]

        if not matching:
            return None

        return max(
            matching,
            key=lambda measurement: (
                measurement.measured_at
            ),
        )


def create_measurement(
    *,
    metric: str,
    value: float,
    age_days: int,
    confidence: str = "high",
) -> PhysiologicalMeasurement:
    return PhysiologicalMeasurement(
        id=uuid4(),
        metric=metric,
        value=value,
        measured_at=(
            REFERENCE_DATE
            - timedelta(days=age_days)
        ),
        protocol="test",
        source="field_test",
        confidence=confidence,
    )


def build_snapshot(
    *,
    athlete=None,
    measurements=(),
):
    if athlete is None:
        athlete = AthleteProfile()

    service = (
        PhysiologicalCalibrationSnapshotService(
            FakeMeasurementRepository(
                measurements
            )
        )
    )

    return service.build(
        athlete_profile_id=uuid4(),
        athlete=athlete,
        reference_date=REFERENCE_DATE,
    )


def test_missing_thresholds_create_single_high_priority_need() -> None:
    snapshot = build_snapshot()

    needs = identify_assessment_needs(
        snapshot
    )

    threshold_needs = [
        need
        for need in needs
        if need.assessment_type
        == "threshold_calibration"
    ]

    assert len(threshold_needs) == 1

    need = threshold_needs[0]

    assert need.priority == "high"

    assert set(need.metrics) == {
        "threshold_heart_rate_1",
        "threshold_heart_rate_2",
    }


def test_missing_vma_is_high_priority() -> None:
    snapshot = build_snapshot()

    needs = identify_assessment_needs(
        snapshot
    )

    need = next(
        need
        for need in needs
        if need.assessment_type
        == "vma_calibration"
    )

    assert need.priority == "high"


def test_legacy_vma_is_medium_priority() -> None:
    athlete = AthleteProfile()

    athlete.physiology.vma = 15.0

    snapshot = build_snapshot(
        athlete=athlete
    )

    needs = identify_assessment_needs(
        snapshot
    )

    need = next(
        need
        for need in needs
        if need.assessment_type
        == "vma_calibration"
    )

    assert need.priority == "medium"


def test_stale_vma_is_high_priority() -> None:
    snapshot = build_snapshot(
        measurements=(
            create_measurement(
                metric="vma",
                value=15.0,
                age_days=220,
            ),
        )
    )

    needs = identify_assessment_needs(
        snapshot
    )

    need = next(
        need
        for need in needs
        if need.assessment_type
        == "vma_calibration"
    )

    assert need.priority == "high"


def test_fresh_metrics_do_not_create_needs() -> None:
    snapshot = build_snapshot(
        measurements=(
            create_measurement(
                metric="vma",
                value=15.5,
                age_days=30,
            ),
            create_measurement(
                metric="max_heart_rate",
                value=190.0,
                age_days=100,
            ),
            create_measurement(
                metric="threshold_heart_rate_1",
                value=145.0,
                age_days=30,
            ),
            create_measurement(
                metric="threshold_heart_rate_2",
                value=170.0,
                age_days=30,
            ),
        )
    )

    needs = identify_assessment_needs(
        snapshot
    )

    assert needs == ()


def test_resting_heart_rate_does_not_create_field_assessment() -> None:
    snapshot = build_snapshot(
        measurements=(
            create_measurement(
                metric="vma",
                value=15.5,
                age_days=30,
            ),
            create_measurement(
                metric="max_heart_rate",
                value=190.0,
                age_days=100,
            ),
            create_measurement(
                metric="threshold_heart_rate_1",
                value=145.0,
                age_days=30,
            ),
            create_measurement(
                metric="threshold_heart_rate_2",
                value=170.0,
                age_days=30,
            ),
        )
    )

    needs = identify_assessment_needs(
        snapshot
    )

    assert all(
        "resting_heart_rate"
        not in need.metrics
        for need in needs
    )


def test_high_priority_needs_are_sorted_first() -> None:
    athlete = AthleteProfile()

    athlete.physiology.vma = 15.0

    snapshot = build_snapshot(
        athlete=athlete
    )

    needs = identify_assessment_needs(
        snapshot
    )

    priorities = [
        need.priority
        for need in needs
    ]

    first_medium = (
        priorities.index("medium")
        if "medium" in priorities
        else len(priorities)
    )

    assert all(
        priority == "high"
        for priority in priorities[
            :first_medium
        ]
    )
