from datetime import date
from uuid import uuid4

from opencoach.coaching.daily_session_rescheduling_service import (
    DailySessionReschedulingService,
)
from opencoach.models import (
    AthleteConstraint,
    AthleteProfile,
    TrainingSession,
)


WEDNESDAY = date(
    2026,
    8,
    26,
)


class FakeTrainingSessionRepository:
    def __init__(
        self,
        sessions: tuple[
            TrainingSession,
            ...
        ],
    ) -> None:
        self.sessions = sessions
        self.calls = []

    def list_sessions_between(
        self,
        athlete_profile_id,
        start_date,
        end_date,
    ):
        self.calls.append(
            (
                athlete_profile_id,
                start_date,
                end_date,
            )
        )

        return list(
            self.sessions
        )


class FakeConstraintRepository:
    def __init__(
        self,
        constraints: tuple[
            AthleteConstraint,
            ...
        ] = (),
    ) -> None:
        self.constraints = constraints
        self.calls = []

    def list_overlapping(
        self,
        athlete_profile_id,
        start_date,
        end_date,
    ):
        self.calls.append(
            (
                athlete_profile_id,
                start_date,
                end_date,
            )
        )

        return list(
            self.constraints
        )


def _athlete() -> AthleteProfile:
    athlete = AthleteProfile()

    athlete.training.available_days = [
        0,
        2,
        4,
        6,
    ]

    return athlete


def _session() -> TrainingSession:
    return TrainingSession(
        id=uuid4(),
        date=WEDNESDAY,
        type="threshold",
        sport_type="Run",
        title="Séance seuil",
        description="",
        duration_minutes=60,
        intensity="hard",
        status="skipped",
    )


def test_service_proposes_future_rescheduling() -> None:
    athlete_profile_id = uuid4()
    session = _session()

    training_repository = (
        FakeTrainingSessionRepository(
            (
                session,
            )
        )
    )

    constraint_repository = (
        FakeConstraintRepository()
    )

    service = DailySessionReschedulingService(
        training_session_repository=(
            training_repository
        ),
        athlete_constraint_repository=(
            constraint_repository
        ),
    )

    result = service.propose(
        athlete_profile_id=athlete_profile_id,
        athlete=_athlete(),
        session=session,
    )

    assert result is not None

    assert (
        result.suggested_date
        > WEDNESDAY
    )

    assert training_repository.calls == [
        (
            athlete_profile_id,
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
    ]

    assert constraint_repository.calls == [
        (
            athlete_profile_id,
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
    ]


def test_service_respects_future_constraint() -> None:
    athlete_profile_id = uuid4()
    session = _session()

    friday = date(
        2026,
        8,
        28,
    )

    constraint = AthleteConstraint(
        id=uuid4(),
        start_date=friday,
        end_date=friday,
        constraint_type="personal",
        availability="unavailable",
        running_allowed=False,
        cross_training_allowed=False,
    )

    service = DailySessionReschedulingService(
        training_session_repository=(
            FakeTrainingSessionRepository(
                (
                    session,
                )
            )
        ),
        athlete_constraint_repository=(
            FakeConstraintRepository(
                (
                    constraint,
                )
            )
        ),
    )

    result = service.propose(
        athlete_profile_id=athlete_profile_id,
        athlete=_athlete(),
        session=session,
    )

    if result is not None:
        assert (
            result.suggested_date
            != friday
        )
