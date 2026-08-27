from datetime import date
from uuid import uuid4

import pytest

from opencoach.coaching.daily_session_replanning import (
    DailyReplanningAction,
)
from opencoach.coaching.daily_session_replanning_application import (
    DailySessionReplanningApplicationService,
    DailySessionReplanningInvalidSourceError,
    DailySessionReplanningOptionUnavailableError,
)
from opencoach.coaching.daily_session_replanning_service import (
    DailySessionReplanningService,
)
from opencoach.models import (
    AthleteProfile,
    TrainingSession,
)


THURSDAY = date(
    2026,
    8,
    27,
)

FRIDAY = date(
    2026,
    8,
    28,
)

SATURDAY = date(
    2026,
    8,
    29,
)

SUNDAY = date(
    2026,
    8,
    30,
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


def _session(
    *,
    session_date: date,
    session_type: str,
    intensity: str,
    status: str = "planned",
    duration_minutes: int = 60,
) -> TrainingSession:
    return TrainingSession(
        id=uuid4(),
        date=session_date,
        type=session_type,
        sport_type="Run",
        title=session_type,
        description="",
        duration_minutes=duration_minutes,
        intensity=intensity,
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
                for session in self.sessions
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
            for session in self.sessions
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


class FakeConstraintRepository:
    def list_overlapping(
        self,
        athlete_profile_id,
        start_date,
        end_date,
    ):
        del athlete_profile_id
        del start_date
        del end_date

        return []


def _scenario():
    source = _session(
        session_date=THURSDAY,
        session_type="threshold",
        intensity="hard",
        status="skipped",
    )

    friday_easy = _session(
        session_date=FRIDAY,
        session_type="aerobic_easy",
        intensity="easy",
        duration_minutes=45,
    )

    sunday_trail = _session(
        session_date=SUNDAY,
        session_type="long_endurance",
        intensity="hard",
        duration_minutes=120,
    )

    repository = (
        FakeTrainingSessionRepository(
            (
                source,
                friday_easy,
                sunday_trail,
            )
        )
    )

    replanning_service = (
        DailySessionReplanningService(
            training_session_repository=(
                repository
            ),
            athlete_constraint_repository=(
                FakeConstraintRepository()
            ),
        )
    )

    application = (
        DailySessionReplanningApplicationService(
            training_session_repository=(
                repository
            ),
            replanning_service=(
                replanning_service
            ),
        )
    )

    return (
        source,
        repository,
        application,
    )


def test_cancel_creates_no_new_session() -> None:
    source, repository, application = (
        _scenario()
    )

    result = application.apply(
        athlete_profile_id=uuid4(),
        athlete=_athlete(),
        source_session_id=source.id,
        action=(
            DailyReplanningAction.CANCEL
        ),
    )

    assert result.cancelled is True
    assert result.created is False
    assert result.applied_session is None

    assert repository.saved == []

    assert source.status == "skipped"


def test_move_unchanged_creates_original_session_on_saturday() -> None:
    source, repository, application = (
        _scenario()
    )

    result = application.apply(
        athlete_profile_id=uuid4(),
        athlete=_athlete(),
        source_session_id=source.id,
        action=(
            DailyReplanningAction
            .MOVE_UNCHANGED
        ),
        target_date=SATURDAY,
    )

    assert result.created is True
    assert result.cancelled is False

    assert result.applied_session is not None

    session = result.applied_session

    assert session.date == SATURDAY

    assert session.type == "threshold"
    assert session.intensity == "hard"
    assert session.duration_minutes == 60

    assert session.status == "planned"

    assert source.status == "skipped"

    assert len(repository.saved) == 1


def test_move_adapted_creates_easy_session_on_saturday() -> None:
    source, repository, application = (
        _scenario()
    )

    result = application.apply(
        athlete_profile_id=uuid4(),
        athlete=_athlete(),
        source_session_id=source.id,
        action=(
            DailyReplanningAction
            .MOVE_ADAPTED
        ),
        target_date=SATURDAY,
    )

    assert result.created is True

    assert result.applied_session is not None

    session = result.applied_session

    assert session.date == SATURDAY

    assert (
        session.type
        == "aerobic_easy"
    )

    assert (
        session.intensity
        == "easy"
    )

    assert (
        session.duration_minutes
        <= 45
    )

    assert session.status == "planned"

    assert source.status == "skipped"


def test_application_is_idempotent() -> None:
    source, repository, application = (
        _scenario()
    )

    athlete_profile_id = uuid4()

    first = application.apply(
        athlete_profile_id=(
            athlete_profile_id
        ),
        athlete=_athlete(),
        source_session_id=source.id,
        action=(
            DailyReplanningAction
            .MOVE_ADAPTED
        ),
        target_date=SATURDAY,
    )

    second = application.apply(
        athlete_profile_id=(
            athlete_profile_id
        ),
        athlete=_athlete(),
        source_session_id=source.id,
        action=(
            DailyReplanningAction
            .MOVE_ADAPTED
        ),
        target_date=SATURDAY,
    )

    assert first.created is True
    assert second.created is False

    assert (
        first.applied_session is not None
    )

    assert (
        second.applied_session is not None
    )

    assert (
        first.applied_session.id
        == second.applied_session.id
    )

    assert len(repository.saved) == 1


def test_obsolete_target_date_is_rejected() -> None:
    source, _, application = (
        _scenario()
    )

    with pytest.raises(
        DailySessionReplanningOptionUnavailableError
    ):
        application.apply(
            athlete_profile_id=uuid4(),
            athlete=_athlete(),
            source_session_id=source.id,
            action=(
                DailyReplanningAction
                .MOVE_ADAPTED
            ),
            target_date=FRIDAY,
        )


def test_planned_source_is_rejected() -> None:
    source, repository, application = (
        _scenario()
    )

    source.status = "planned"

    with pytest.raises(
        DailySessionReplanningInvalidSourceError
    ):
        application.apply(
            athlete_profile_id=uuid4(),
            athlete=_athlete(),
            source_session_id=source.id,
            action=(
                DailyReplanningAction.CANCEL
            ),
        )

    assert repository.saved == []
