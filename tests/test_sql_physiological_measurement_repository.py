from datetime import date
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from opencoach.database.base import Base
from opencoach.database.models import (
    AthleteProfile,
    User,
)
from opencoach.database.repositories import (
    PhysiologicalMeasurementRepositoryError,
    SqlPhysiologicalMeasurementRepository,
)
from opencoach.models import (
    PhysiologicalMeasurement,
)


def create_session():
    engine = create_engine(
        "sqlite:///:memory:",
    )

    Base.metadata.create_all(
        engine
    )

    SessionLocal = sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )

    return SessionLocal()


def create_profile(
    db,
) -> AthleteProfile:
    user = User(
        email=f"{uuid4()}@opencoach.local",
    )

    profile = AthleteProfile(
        user=user,
        first_name="Test",
        last_name="Athlete",
    )

    db.add(
        profile
    )

    db.commit()

    return profile


def create_measurement(
    *,
    metric: str = "vma",
    value: float = 15.0,
    measured_at: date = date(
        2026,
        8,
        1,
    ),
    protocol: str | None = "vameval",
) -> PhysiologicalMeasurement:
    return PhysiologicalMeasurement(
        id=uuid4(),
        metric=metric,
        value=value,
        measured_at=measured_at,
        protocol=protocol,
        source="field_test",
        confidence="high",
    )


def test_measurement_can_be_saved_and_loaded() -> None:
    db = create_session()

    try:
        profile = create_profile(
            db
        )

        repository = (
            SqlPhysiologicalMeasurementRepository(
                db
            )
        )

        measurement = create_measurement()

        saved = repository.save_measurement(
            profile.id,
            measurement,
        )

        loaded = repository.get_measurement(
            profile.id,
            saved.id,
        )

        assert loaded is not None

        assert loaded.id == measurement.id
        assert loaded.metric == "vma"
        assert loaded.value == 15.0
        assert loaded.protocol == "vameval"

    finally:
        db.close()


def test_existing_measurement_can_be_updated() -> None:
    db = create_session()

    try:
        profile = create_profile(
            db
        )

        repository = (
            SqlPhysiologicalMeasurementRepository(
                db
            )
        )

        original = create_measurement(
            value=15.0,
        )

        repository.save_measurement(
            profile.id,
            original,
        )

        updated = PhysiologicalMeasurement(
            id=original.id,
            metric="vma",
            value=15.5,
            measured_at=original.measured_at,
            protocol="half_cooper",
            source="field_test",
            confidence="medium",
        )

        saved = repository.save_measurement(
            profile.id,
            updated,
        )

        assert saved.id == original.id
        assert saved.value == 15.5
        assert saved.protocol == "half_cooper"
        assert saved.confidence == "medium"

    finally:
        db.close()


def test_measurements_are_sorted_newest_first() -> None:
    db = create_session()

    try:
        profile = create_profile(
            db
        )

        repository = (
            SqlPhysiologicalMeasurementRepository(
                db
            )
        )

        old = create_measurement(
            value=14.5,
            measured_at=date(
                2026,
                1,
                10,
            ),
        )

        recent = create_measurement(
            value=15.5,
            measured_at=date(
                2026,
                8,
                1,
            ),
        )

        repository.save_measurement(
            profile.id,
            old,
        )

        repository.save_measurement(
            profile.id,
            recent,
        )

        measurements = (
            repository.list_measurements(
                profile.id
            )
        )

        assert measurements == [
            recent,
            old,
        ]

    finally:
        db.close()


def test_list_measurements_by_metric_filters_history() -> None:
    db = create_session()

    try:
        profile = create_profile(
            db
        )

        repository = (
            SqlPhysiologicalMeasurementRepository(
                db
            )
        )

        vma = create_measurement(
            metric="vma",
            value=15.0,
        )

        max_hr = create_measurement(
            metric="max_heart_rate",
            value=190.0,
            protocol=None,
        )

        repository.save_measurement(
            profile.id,
            vma,
        )

        repository.save_measurement(
            profile.id,
            max_hr,
        )

        measurements = (
            repository.list_measurements_by_metric(
                profile.id,
                "vma",
            )
        )

        assert measurements == [
            vma,
        ]

    finally:
        db.close()


def test_get_latest_measurement_returns_newest() -> None:
    db = create_session()

    try:
        profile = create_profile(
            db
        )

        repository = (
            SqlPhysiologicalMeasurementRepository(
                db
            )
        )

        old = create_measurement(
            value=14.5,
            measured_at=date(
                2026,
                1,
                10,
            ),
        )

        recent = create_measurement(
            value=15.5,
            measured_at=date(
                2026,
                8,
                1,
            ),
        )

        repository.save_measurement(
            profile.id,
            old,
        )

        repository.save_measurement(
            profile.id,
            recent,
        )

        latest = repository.get_latest_measurement(
            profile.id,
            "vma",
        )

        assert latest == recent

    finally:
        db.close()


def test_measurement_can_be_deleted() -> None:
    db = create_session()

    try:
        profile = create_profile(
            db
        )

        repository = (
            SqlPhysiologicalMeasurementRepository(
                db
            )
        )

        measurement = create_measurement()

        repository.save_measurement(
            profile.id,
            measurement,
        )

        repository.delete_measurement(
            profile.id,
            measurement.id,
        )

        assert repository.get_measurement(
            profile.id,
            measurement.id,
        ) is None

    finally:
        db.close()


def test_delete_unknown_measurement_raises_error() -> None:
    db = create_session()

    try:
        profile = create_profile(
            db
        )

        repository = (
            SqlPhysiologicalMeasurementRepository(
                db
            )
        )

        with pytest.raises(
            PhysiologicalMeasurementRepositoryError,
            match="introuvable",
        ):
            repository.delete_measurement(
                profile.id,
                uuid4(),
            )

    finally:
        db.close()
