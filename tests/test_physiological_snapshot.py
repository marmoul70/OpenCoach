from datetime import date, timedelta
from uuid import uuid4

from opencoach.models import (
    AthleteProfile,
    PhysiologicalMeasurement,
)
from opencoach.planning import (
    PhysiologicalCalibrationSnapshotService,
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


def test_uses_latest_historical_measurement() -> None:
    old = create_measurement(
        metric="vma",
        value=14.8,
        age_days=200,
    )

    recent = create_measurement(
        metric="vma",
        value=15.6,
        age_days=40,
    )

    service = (
        PhysiologicalCalibrationSnapshotService(
            FakeMeasurementRepository(
                (
                    old,
                    recent,
                )
            )
        )
    )

    snapshot = service.build(
        athlete_profile_id=uuid4(),
        athlete=AthleteProfile(),
        reference_date=REFERENCE_DATE,
    )

    assert snapshot.vma.value == 15.6
    assert snapshot.vma.source == "history"

    assert snapshot.vma.measurement == (
        recent
    )

    assert snapshot.vma.freshness is not None

    assert (
        snapshot.vma.freshness.freshness
        == "fresh"
    )

    assert snapshot.vma.usable is True


def test_legacy_profile_value_is_preserved() -> None:
    athlete = AthleteProfile()

    athlete.physiology.vma = 15.0

    service = (
        PhysiologicalCalibrationSnapshotService(
            FakeMeasurementRepository()
        )
    )

    snapshot = service.build(
        athlete_profile_id=uuid4(),
        athlete=athlete,
        reference_date=REFERENCE_DATE,
    )

    assert snapshot.vma.value == 15.0

    assert snapshot.vma.source == (
        "legacy_profile"
    )

    assert snapshot.vma.usable is True

    assert (
        snapshot.vma.recalibration_recommended
        is True
    )

    assert snapshot.vma.freshness is None


def test_missing_metric_is_not_usable() -> None:
    service = (
        PhysiologicalCalibrationSnapshotService(
            FakeMeasurementRepository()
        )
    )

    snapshot = service.build(
        athlete_profile_id=uuid4(),
        athlete=AthleteProfile(),
        reference_date=REFERENCE_DATE,
    )

    assert snapshot.vma.source == "missing"
    assert snapshot.vma.value is None

    assert snapshot.vma.usable is False

    assert (
        snapshot.vma.recalibration_recommended
        is True
    )


def test_stale_measurement_requires_recalibration() -> None:
    measurement = create_measurement(
        metric="vma",
        value=15.0,
        age_days=220,
    )

    service = (
        PhysiologicalCalibrationSnapshotService(
            FakeMeasurementRepository(
                (measurement,)
            )
        )
    )

    snapshot = service.build(
        athlete_profile_id=uuid4(),
        athlete=AthleteProfile(),
        reference_date=REFERENCE_DATE,
    )

    assert snapshot.vma.source == "history"

    assert snapshot.vma.usable is False

    assert (
        snapshot.vma.recalibration_recommended
        is True
    )


def test_snapshot_exposes_missing_metrics() -> None:
    athlete = AthleteProfile()

    athlete.physiology.vma = 15.0

    service = (
        PhysiologicalCalibrationSnapshotService(
            FakeMeasurementRepository()
        )
    )

    snapshot = service.build(
        athlete_profile_id=uuid4(),
        athlete=athlete,
        reference_date=REFERENCE_DATE,
    )

    missing_names = {
        metric.metric
        for metric in snapshot.missing_metrics
    }

    assert "vma" not in missing_names

    assert "max_heart_rate" in missing_names
    assert "threshold_heart_rate_1" in missing_names
    assert "threshold_heart_rate_2" in missing_names


def test_snapshot_exposes_recalibration_needs() -> None:
    athlete = AthleteProfile()

    athlete.physiology.vma = 15.0

    service = (
        PhysiologicalCalibrationSnapshotService(
            FakeMeasurementRepository()
        )
    )

    snapshot = service.build(
        athlete_profile_id=uuid4(),
        athlete=athlete,
        reference_date=REFERENCE_DATE,
    )

    recalibration_names = {
        metric.metric
        for metric in snapshot.recalibration_metrics
    }

    assert "vma" in recalibration_names

    assert snapshot.has_calibration_needs is True


def test_fresh_complete_history_has_no_calibration_need() -> None:
    measurements = (
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
            metric="resting_heart_rate",
            value=48.0,
            age_days=10,
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

    service = (
        PhysiologicalCalibrationSnapshotService(
            FakeMeasurementRepository(
                measurements
            )
        )
    )

    snapshot = service.build(
        athlete_profile_id=uuid4(),
        athlete=AthleteProfile(),
        reference_date=REFERENCE_DATE,
    )

    assert snapshot.missing_metrics == ()

    assert (
        snapshot.recalibration_metrics
        == ()
    )

    assert (
        len(snapshot.usable_metrics)
        == 5
    )

    assert snapshot.has_calibration_needs is False
