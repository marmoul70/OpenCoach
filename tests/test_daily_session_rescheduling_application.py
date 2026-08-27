from datetime import date
from uuid import uuid4

import pytest

from opencoach.coaching.daily_session_rescheduling import (
    DailySessionReschedulingProposal,
)
from opencoach.coaching.daily_session_rescheduling_application import (
    DailySessionReschedulingApplicationService,
    DailySessionReschedulingInvalidSourceError,
    DailySessionReschedulingUnavailableError,
)
from opencoach.models import (
    AthleteProfile,
    TrainingSession,
)


SOURCE_DATE = date(
    2026,
    8,
    26,
)

TARGET_DATE = date(
    2026,
    8,
    28,
)


def _source(
    *,
    status: str = "skipped",
) -> TrainingSession:
    return TrainingSession(
        id=uuid4(),
        date=SOURCE_DATE,
        type="threshold",
        sport_type="Run",
        title="Séance seuil",
        description="Séance qualitative.",
        duration_minutes=60,
        planning_key=(
            "2026-08-24:threshold"
        ),
        intensity="hard",
        status=status,
    )


class FakeTrainingSessionRepository:
    def __init__(
        self,
        sessions,
    ) -> None:
        self.sessions = list(
            sessions
        )

        self.saved = []

    def get_session(
        self,
        athlete_profile_id,
        session_id,
    ):
        del athlete_profile_id

        return next(
            (
                session
                for session
                in self.sessions
                if session.id == session_id
            ),
            None,
        )

    def list_sessions_between(
        self,
        athlete_profile_id,
        start_date,
        end_date,
    ):
        del athlete_profile_id

        return [
            session
            for session
            in self.sessions
            if (
                start_date
                <= session.date
                <= end_date
            )
        ]

    def save_session(
        self,
        athlete_profile_id,
        session,
    ):
        del athlete_profile_id

        saved = TrainingSession(
            id=(
                session.id
                if session.id is not None
                else uuid4()
            ),
            date=session.date,
            type=session.type,
            sport_type=session.sport_type,
            title=session.title,
            description=session.description,
            duration_minutes=(
                session.duration_minutes
            ),
            planning_key=(
                session.planning_key
            ),
            distance_km=session.distance_km,
            elevation_gain_m=(
                session.elevation_gain_m
            ),
            intensity=session.intensity,
            heart_rate_zone=(
                session.heart_rate_zone
            ),
            status=session.status,
            activity_id=session.activity_id,
        )

        self.sessions.append(
            saved
        )

        self.saved.append(
            saved
        )

        return saved


class FakeReschedulingService:
    def __init__(
        self,
        *,
        available: bool = True,
    ) -> None:
        self.available = available

    def propose(
        self,
        *,
        athlete_profile_id,
        athlete,
        session,
    ):
        del athlete_profile_id
        del athlete

        if not self.available:
            return None

        return DailySessionReschedulingProposal(
            original_session=session,
            suggested_date=TARGET_DATE,
            requires_confirmation=True,
            reasons=(
                "Créneau futur compatible.",
            ),
        )


def _service(
    repository,
    *,
    available: bool = True,
):
    return (
        DailySessionReschedulingApplicationService(
            training_session_repository=(
                repository
            ),
            rescheduling_service=(
                FakeReschedulingService(
                    available=available
                )
            ),
        )
    )


def test_apply_creates_new_planned_occurrence() -> None:
    source = _source()

    repository = (
        FakeTrainingSessionRepository(
            (
                source,
            )
        )
    )

    result = _service(
        repository
    ).apply(
        athlete_profile_id=uuid4(),
        athlete=AthleteProfile(),
        source_session_id=source.id,
    )

    assert result.created is True

    assert (
        result.source_session.status
        == "skipped"
    )

    assert (
        result.rescheduled_session.id
        != source.id
    )

    assert (
        result.rescheduled_session.date
        == TARGET_DATE
    )

    assert (
        result.rescheduled_session.status
        == "planned"
    )

    assert (
        result.rescheduled_session.activity_id
        is None
    )

    assert (
        result.rescheduled_session.planning_key
        != source.planning_key
    )

    assert (
        result.rescheduled_session.planning_key
        == (
            "2026-08-24:"
            f"rescheduled-{source.id}"
        )
    )


def test_source_skipped_session_remains_unchanged() -> None:
    source = _source()

    repository = (
        FakeTrainingSessionRepository(
            (
                source,
            )
        )
    )

    _service(
        repository
    ).apply(
        athlete_profile_id=uuid4(),
        athlete=AthleteProfile(),
        source_session_id=source.id,
    )

    assert source.status == "skipped"

    assert source.date == SOURCE_DATE

    assert (
        source.planning_key
        == "2026-08-24:threshold"
    )


def test_apply_is_idempotent() -> None:
    source = _source()

    repository = (
        FakeTrainingSessionRepository(
            (
                source,
            )
        )
    )

    service = _service(
        repository
    )

    athlete_profile_id = uuid4()

    first = service.apply(
        athlete_profile_id=(
            athlete_profile_id
        ),
        athlete=AthleteProfile(),
        source_session_id=source.id,
    )

    second = service.apply(
        athlete_profile_id=(
            athlete_profile_id
        ),
        athlete=AthleteProfile(),
        source_session_id=source.id,
    )

    assert first.created is True
    assert second.created is False

    assert (
        first.rescheduled_session.id
        == second.rescheduled_session.id
    )

    assert len(repository.saved) == 1


def test_non_skipped_source_is_rejected() -> None:
    source = _source(
        status="planned",
    )

    repository = (
        FakeTrainingSessionRepository(
            (
                source,
            )
        )
    )

    with pytest.raises(
        DailySessionReschedulingInvalidSourceError
    ):
        _service(
            repository
        ).apply(
            athlete_profile_id=uuid4(),
            athlete=AthleteProfile(),
            source_session_id=source.id,
        )


def test_missing_current_proposal_is_rejected() -> None:
    source = _source()

    repository = (
        FakeTrainingSessionRepository(
            (
                source,
            )
        )
    )

    with pytest.raises(
        DailySessionReschedulingUnavailableError
    ):
        _service(
            repository,
            available=False,
        ).apply(
            athlete_profile_id=uuid4(),
            athlete=AthleteProfile(),
            source_session_id=source.id,
        )
