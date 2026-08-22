from datetime import date
from uuid import uuid4

from opencoach.models import (
    AthleteProfile,
    PhysiologicalMeasurement,
)
from opencoach.services import (
    PhysiologicalMeasurementService,
)


class FakeMeasurementRepository:
    def __init__(self) -> None:
        self.measurements = []

    def save_measurement(
        self,
        athlete_profile_id,
        measurement,
    ):
        self.measurements.append(
            measurement
        )

        return measurement

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


class FakeProfileService:
    def __init__(
        self,
        athlete: AthleteProfile,
    ) -> None:
        self.athlete = athlete
        self.updated_profile = None

    def get_profile(self) -> AthleteProfile:
        return self.athlete

    def update_profile(
        self,
        profile: AthleteProfile,
    ) -> AthleteProfile:
        self.updated_profile = profile
        self.athlete = profile

        return profile


def create_measurement(
    *,
    metric: str,
    value: float,
    measured_at: date,
) -> PhysiologicalMeasurement:
    return PhysiologicalMeasurement(
        id=uuid4(),
        metric=metric,
        value=value,
        measured_at=measured_at,
        source="field_test",
        confidence="high",
    )


def test_latest_vma_updates_profile() -> None:
    athlete = AthleteProfile()

    profile_service = FakeProfileService(
        athlete
    )

    repository = FakeMeasurementRepository()

    service = PhysiologicalMeasurementService(
        measurement_repository=repository,
        profile_service=profile_service,
    )

    measurement = create_measurement(
        metric="vma",
        value=15.6,
        measured_at=date(
            2026,
            8,
            22,
        ),
    )

    service.record_measurement(
        athlete_profile_id=uuid4(),
        measurement=measurement,
    )

    assert athlete.physiology.vma == 15.6

    assert (
        profile_service.updated_profile
        is athlete
    )


def test_old_measurement_does_not_replace_current_value() -> None:
    athlete = AthleteProfile()

    athlete.physiology.vma = 15.6

    profile_service = FakeProfileService(
        athlete
    )

    repository = FakeMeasurementRepository()

    recent = create_measurement(
        metric="vma",
        value=15.6,
        measured_at=date(
            2026,
            8,
            22,
        ),
    )

    repository.save_measurement(
        uuid4(),
        recent,
    )

    service = PhysiologicalMeasurementService(
        measurement_repository=repository,
        profile_service=profile_service,
    )

    old = create_measurement(
        metric="vma",
        value=14.8,
        measured_at=date(
            2026,
            1,
            10,
        ),
    )

    service.record_measurement(
        athlete_profile_id=uuid4(),
        measurement=old,
    )

    assert athlete.physiology.vma == 15.6

    assert (
        profile_service.updated_profile
        is None
    )


def test_max_heart_rate_updates_profile() -> None:
    athlete = AthleteProfile()

    service = PhysiologicalMeasurementService(
        measurement_repository=(
            FakeMeasurementRepository()
        ),
        profile_service=FakeProfileService(
            athlete
        ),
    )

    measurement = create_measurement(
        metric="max_heart_rate",
        value=191.4,
        measured_at=date(
            2026,
            8,
            22,
        ),
    )

    service.record_measurement(
        athlete_profile_id=uuid4(),
        measurement=measurement,
    )

    assert (
        athlete.physiology.max_heart_rate
        == 191
    )


def test_resting_heart_rate_updates_profile() -> None:
    athlete = AthleteProfile()

    service = PhysiologicalMeasurementService(
        measurement_repository=(
            FakeMeasurementRepository()
        ),
        profile_service=FakeProfileService(
            athlete
        ),
    )

    measurement = create_measurement(
        metric="resting_heart_rate",
        value=48.2,
        measured_at=date(
            2026,
            8,
            22,
        ),
    )

    service.record_measurement(
        athlete_profile_id=uuid4(),
        measurement=measurement,
    )

    assert (
        athlete.physiology.resting_heart_rate
        == 48
    )


def test_sv1_updates_profile() -> None:
    athlete = AthleteProfile()

    service = PhysiologicalMeasurementService(
        measurement_repository=(
            FakeMeasurementRepository()
        ),
        profile_service=FakeProfileService(
            athlete
        ),
    )

    measurement = create_measurement(
        metric="threshold_heart_rate_1",
        value=148.0,
        measured_at=date(
            2026,
            8,
            22,
        ),
    )

    service.record_measurement(
        athlete_profile_id=uuid4(),
        measurement=measurement,
    )

    assert (
        athlete.physiology.threshold_heart_rate_1
        == 148
    )


def test_sv2_updates_profile() -> None:
    athlete = AthleteProfile()

    service = PhysiologicalMeasurementService(
        measurement_repository=(
            FakeMeasurementRepository()
        ),
        profile_service=FakeProfileService(
            athlete
        ),
    )

    measurement = create_measurement(
        metric="threshold_heart_rate_2",
        value=172.0,
        measured_at=date(
            2026,
            8,
            22,
        ),
    )

    service.record_measurement(
        athlete_profile_id=uuid4(),
        measurement=measurement,
    )

    assert (
        athlete.physiology.threshold_heart_rate_2
        == 172
    )
