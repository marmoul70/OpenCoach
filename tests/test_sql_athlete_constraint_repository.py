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
    AthleteConstraintRepositoryError,
    SqlAthleteConstraintRepository,
)
from opencoach.models import AthleteConstraint


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


def create_constraint(
    *,
    start_date: date,
    end_date: date,
    constraint_type: str = "work",
    availability: str = "unavailable",
    running_allowed: bool = True,
    cross_training_allowed: bool = True,
    max_duration_minutes: int | None = None,
    notes: str | None = None,
) -> AthleteConstraint:
    return AthleteConstraint(
        id=uuid4(),
        start_date=start_date,
        end_date=end_date,
        constraint_type=constraint_type,
        availability=availability,
        running_allowed=running_allowed,
        cross_training_allowed=cross_training_allowed,
        max_duration_minutes=max_duration_minutes,
        notes=notes,
    )


def test_constraint_can_be_saved_and_loaded() -> None:
    db = create_session()

    try:
        profile = create_profile(
            db
        )

        repository = (
            SqlAthleteConstraintRepository(
                db
            )
        )

        constraint = create_constraint(
            start_date=date(
                2026,
                8,
                24,
            ),
            end_date=date(
                2026,
                8,
                30,
            ),
            constraint_type="injury",
            availability="limited",
            running_allowed=False,
            cross_training_allowed=True,
            notes="Pas de course pendant une semaine.",
        )

        saved = repository.save_constraint(
            profile.id,
            constraint,
        )

        loaded = repository.get_constraint(
            profile.id,
            saved.id,
        )

        assert loaded is not None

        assert loaded.id == constraint.id
        assert loaded.start_date == constraint.start_date
        assert loaded.end_date == constraint.end_date

        assert loaded.constraint_type == "injury"
        assert loaded.availability == "limited"

        assert loaded.running_allowed is False

        assert (
            loaded.cross_training_allowed
            is True
        )

        assert loaded.notes == (
            "Pas de course pendant une semaine."
        )

    finally:
        db.close()


def test_existing_constraint_can_be_updated() -> None:
    db = create_session()

    try:
        profile = create_profile(
            db
        )

        repository = (
            SqlAthleteConstraintRepository(
                db
            )
        )

        original = create_constraint(
            start_date=date(
                2026,
                8,
                26,
            ),
            end_date=date(
                2026,
                8,
                26,
            ),
        )

        repository.save_constraint(
            profile.id,
            original,
        )

        updated = AthleteConstraint(
            id=original.id,
            start_date=original.start_date,
            end_date=original.end_date,
            constraint_type="work",
            availability="limited",
            running_allowed=True,
            cross_training_allowed=True,
            max_duration_minutes=45,
            notes="45 minutes maximum.",
        )

        saved = repository.save_constraint(
            profile.id,
            updated,
        )

        assert saved.id == original.id
        assert saved.availability == "limited"

        assert (
            saved.max_duration_minutes
            == 45
        )

        assert saved.notes == (
            "45 minutes maximum."
        )

    finally:
        db.close()


def test_list_overlapping_returns_matching_constraints() -> None:
    db = create_session()

    try:
        profile = create_profile(
            db
        )

        repository = (
            SqlAthleteConstraintRepository(
                db
            )
        )

        previous_overlap = create_constraint(
            start_date=date(
                2026,
                8,
                23,
            ),
            end_date=date(
                2026,
                8,
                25,
            ),
            constraint_type="travel",
        )

        inside = create_constraint(
            start_date=date(
                2026,
                8,
                27,
            ),
            end_date=date(
                2026,
                8,
                27,
            ),
            constraint_type="work",
        )

        next_overlap = create_constraint(
            start_date=date(
                2026,
                8,
                29,
            ),
            end_date=date(
                2026,
                9,
                2,
            ),
            constraint_type="family",
        )

        outside = create_constraint(
            start_date=date(
                2026,
                9,
                5,
            ),
            end_date=date(
                2026,
                9,
                6,
            ),
        )

        for constraint in (
            previous_overlap,
            inside,
            next_overlap,
            outside,
        ):
            repository.save_constraint(
                profile.id,
                constraint,
            )

        constraints = repository.list_overlapping(
            profile.id,
            date(
                2026,
                8,
                24,
            ),
            date(
                2026,
                8,
                30,
            ),
        )

        ids = {
            constraint.id
            for constraint in constraints
        }

        assert previous_overlap.id in ids
        assert inside.id in ids
        assert next_overlap.id in ids

        assert outside.id not in ids

        assert len(constraints) == 3

    finally:
        db.close()


def test_list_overlapping_is_scoped_to_athlete() -> None:
    db = create_session()

    try:
        first_profile = create_profile(
            db
        )

        second_profile = create_profile(
            db
        )

        repository = (
            SqlAthleteConstraintRepository(
                db
            )
        )

        first_constraint = create_constraint(
            start_date=date(
                2026,
                8,
                27,
            ),
            end_date=date(
                2026,
                8,
                27,
            ),
        )

        second_constraint = create_constraint(
            start_date=date(
                2026,
                8,
                27,
            ),
            end_date=date(
                2026,
                8,
                27,
            ),
        )

        repository.save_constraint(
            first_profile.id,
            first_constraint,
        )

        repository.save_constraint(
            second_profile.id,
            second_constraint,
        )

        constraints = repository.list_overlapping(
            first_profile.id,
            date(
                2026,
                8,
                24,
            ),
            date(
                2026,
                8,
                30,
            ),
        )

        assert len(constraints) == 1

        assert (
            constraints[0].id
            == first_constraint.id
        )

    finally:
        db.close()


def test_constraint_can_be_deleted() -> None:
    db = create_session()

    try:
        profile = create_profile(
            db
        )

        repository = (
            SqlAthleteConstraintRepository(
                db
            )
        )

        constraint = create_constraint(
            start_date=date(
                2026,
                8,
                27,
            ),
            end_date=date(
                2026,
                8,
                27,
            ),
        )

        saved = repository.save_constraint(
            profile.id,
            constraint,
        )

        repository.delete_constraint(
            profile.id,
            saved.id,
        )

        assert repository.get_constraint(
            profile.id,
            saved.id,
        ) is None

    finally:
        db.close()


def test_delete_unknown_constraint_raises_error() -> None:
    db = create_session()

    try:
        profile = create_profile(
            db
        )

        repository = (
            SqlAthleteConstraintRepository(
                db
            )
        )

        with pytest.raises(
            AthleteConstraintRepositoryError,
            match="introuvable",
        ):
            repository.delete_constraint(
                profile.id,
                uuid4(),
            )

    finally:
        db.close()


def test_list_overlapping_rejects_invalid_period() -> None:
    db = create_session()

    try:
        profile = create_profile(
            db
        )

        repository = (
            SqlAthleteConstraintRepository(
                db
            )
        )

        with pytest.raises(
            ValueError,
            match="date de fin",
        ):
            repository.list_overlapping(
                profile.id,
                date(
                    2026,
                    8,
                    30,
                ),
                date(
                    2026,
                    8,
                    24,
                ),
            )

    finally:
        db.close()
