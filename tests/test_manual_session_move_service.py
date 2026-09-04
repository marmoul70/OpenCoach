from datetime import (
    date,
)
from uuid import (
    uuid4,
)

import pytest

from opencoach.coaching.manual_session_move_service import (
    ManualSessionMoveService,
    ManualSessionMoveSessionNotFoundError,
)
from opencoach.models import (
    AthleteProfile,
    TrainingSession,
)


PROFILE_ID = uuid4()

MONDAY = date(
    2026,
    9,
    7,
)


class FakeTrainingSessionRepository:
    def __init__(
        self,
        sessions,
    ):
        self.sessions = list(
            sessions
        )

        self.get_calls = []
        self.list_calls = []

    def get_session(
        self,
        athlete_profile_id,
        session_id,
    ):
        self.get_calls.append(
            (
                athlete_profile_id,
                session_id,
            )
        )

        return next(
            (
                session
                for session
                in self.sessions
                if session.id
                == session_id
            ),
            None,
        )

    def save_session(
        self,
        athlete_profile_id,
        session,
    ):
        return session

    def list_sessions_between(
        self,
        athlete_profile_id,
        start_date,
        end_date,
    ):
        self.list_calls.append(
            (
                athlete_profile_id,
                start_date,
                end_date,
            )
        )

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


class FakeAthleteConstraintRepository:
    def __init__(self):
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

        return []


def make_athlete():
    athlete = AthleteProfile()

    athlete.training.available_days = [
        0,
        1,
        2,
        3,
        4,
        5,
        6,
    ]

    return athlete


def make_strength_session():
    return TrainingSession(
        id=uuid4(),
        date=date(
            2026,
            9,
            8,
        ),
        type="strength_lower_body",
        sport_type="strength",
        title="Renforcement jambes",
        description="",
        duration_minutes=45,
        intensity="moderate",
        status="planned",
        activity_id=None,
    )


def test_preview_builds_complete_week():
    session = (
        make_strength_session()
    )

    training_repository = (
        FakeTrainingSessionRepository(
            [
                session,
            ]
        )
    )

    constraint_repository = (
        FakeAthleteConstraintRepository()
    )

    service = (
        ManualSessionMoveService(
            training_session_repository=(
                training_repository
            ),
            athlete_constraint_repository=(
                constraint_repository
            ),
        )
    )

    result = service.preview(
        athlete_profile_id=(
            PROFILE_ID
        ),
        athlete=make_athlete(),
        session_id=session.id,
        reference_date=date(
            2026,
            9,
            8,
        ),
    )

    assert result.source_date == (
        date(
            2026,
            9,
            8,
        )
    )

    assert result.week_start == (
        MONDAY
    )

    assert result.week_end == date(
        2026,
        9,
        13,
    )

    assert len(
        result.days
    ) == 7


def test_preview_loads_constraints_for_session_week():
    session = (
        make_strength_session()
    )

    training_repository = (
        FakeTrainingSessionRepository(
            [
                session,
            ]
        )
    )

    constraint_repository = (
        FakeAthleteConstraintRepository()
    )

    service = (
        ManualSessionMoveService(
            training_session_repository=(
                training_repository
            ),
            athlete_constraint_repository=(
                constraint_repository
            ),
        )
    )

    service.preview(
        athlete_profile_id=(
            PROFILE_ID
        ),
        athlete=make_athlete(),
        session_id=session.id,
        reference_date=date(
            2026,
            9,
            8,
        ),
    )

    assert (
        constraint_repository.calls
        == [
            (
                PROFILE_ID,
                date(
                    2026,
                    9,
                    7,
                ),
                date(
                    2026,
                    9,
                    13,
                ),
            )
        ]
    )


def test_preview_loads_all_week_sessions():
    session = (
        make_strength_session()
    )

    training_repository = (
        FakeTrainingSessionRepository(
            [
                session,
            ]
        )
    )

    service = (
        ManualSessionMoveService(
            training_session_repository=(
                training_repository
            ),
            athlete_constraint_repository=(
                FakeAthleteConstraintRepository()
            ),
        )
    )

    service.preview(
        athlete_profile_id=(
            PROFILE_ID
        ),
        athlete=make_athlete(),
        session_id=session.id,
        reference_date=date(
            2026,
            9,
            8,
        ),
    )

    assert (
        training_repository.list_calls
        == [
            (
                PROFILE_ID,
                date(
                    2026,
                    9,
                    7,
                ),
                date(
                    2026,
                    9,
                    13,
                ),
            )
        ]
    )


def test_preview_marks_best_day():
    session = (
        make_strength_session()
    )

    training_repository = (
        FakeTrainingSessionRepository(
            [
                session,
            ]
        )
    )

    service = (
        ManualSessionMoveService(
            training_session_repository=(
                training_repository
            ),
            athlete_constraint_repository=(
                FakeAthleteConstraintRepository()
            ),
        )
    )

    result = service.preview(
        athlete_profile_id=(
            PROFILE_ID
        ),
        athlete=make_athlete(),
        session_id=session.id,
        reference_date=date(
            2026,
            9,
            8,
        ),
    )

    recommended = [
        day
        for day
        in result.days
        if day.recommended
    ]

    assert len(
        recommended
    ) == 1

    assert result.best_date == (
        recommended[0].date
    )


def test_preview_unknown_session_raises():
    training_repository = (
        FakeTrainingSessionRepository(
            []
        )
    )

    service = (
        ManualSessionMoveService(
            training_session_repository=(
                training_repository
            ),
            athlete_constraint_repository=(
                FakeAthleteConstraintRepository()
            ),
        )
    )

    with pytest.raises(
        ManualSessionMoveSessionNotFoundError,
        match="Séance introuvable",
    ):
        service.preview(
            athlete_profile_id=(
                PROFILE_ID
            ),
            athlete=make_athlete(),
            session_id=uuid4(),
            reference_date=date(
                2026,
                9,
                8,
            ),
        )

def test_move_changes_date_and_keeps_identity():
    session = (
        make_strength_session()
    )

    repository = (
        FakeTrainingSessionRepository(
            [
                session,
            ]
        )
    )

    service = (
        ManualSessionMoveService(
            training_session_repository=(
                repository
            ),
            athlete_constraint_repository=(
                FakeAthleteConstraintRepository()
            ),
        )
    )

    original_id = session.id

    moved = service.move(
        athlete_profile_id=(
            PROFILE_ID
        ),
        athlete=make_athlete(),
        session_id=session.id,
        target_date=date(
            2026,
            9,
            9,
        ),
        reference_date=date(
            2026,
            9,
            8,
        ),
    )

    assert moved.id == original_id

    assert moved.date == date(
        2026,
        9,
        9,
    )

    assert moved.status == "planned"


def test_move_refuses_current_date():
    session = (
        make_strength_session()
    )

    service = (
        ManualSessionMoveService(
            training_session_repository=(
                FakeTrainingSessionRepository(
                    [
                        session,
                    ]
                )
            ),
            athlete_constraint_repository=(
                FakeAthleteConstraintRepository()
            ),
        )
    )

    from opencoach.coaching.manual_session_move_service import (
        ManualSessionMoveTargetUnavailableError,
    )

    with pytest.raises(
        ManualSessionMoveTargetUnavailableError,
        match="déjà prévue",
    ):
        service.move(
            athlete_profile_id=(
                PROFILE_ID
            ),
            athlete=make_athlete(),
            session_id=session.id,
            target_date=session.date,
            reference_date=date(
                2026,
                9,
                8,
            ),
        )


def test_move_refuses_outside_week():
    session = (
        make_strength_session()
    )

    service = (
        ManualSessionMoveService(
            training_session_repository=(
                FakeTrainingSessionRepository(
                    [
                        session,
                    ]
                )
            ),
            athlete_constraint_repository=(
                FakeAthleteConstraintRepository()
            ),
        )
    )

    from opencoach.coaching.manual_session_move_service import (
        ManualSessionMoveTargetUnavailableError,
    )

    with pytest.raises(
        ManualSessionMoveTargetUnavailableError,
        match="hors de la semaine",
    ):
        service.move(
            athlete_profile_id=(
                PROFILE_ID
            ),
            athlete=make_athlete(),
            session_id=session.id,
            target_date=date(
                2026,
                9,
                14,
            ),
            reference_date=date(
                2026,
                9,
                8,
            ),
        )


def test_move_refuses_blocked_day():
    session = (
        make_strength_session()
    )

    long_run = TrainingSession(
        id=uuid4(),
        date=date(
            2026,
            9,
            12,
        ),
        type="long_endurance",
        sport_type="run",
        title="Sortie longue",
        description="",
        duration_minutes=120,
        intensity="easy",
        status="planned",
        activity_id=None,
    )

    service = (
        ManualSessionMoveService(
            training_session_repository=(
                FakeTrainingSessionRepository(
                    [
                        session,
                        long_run,
                    ]
                )
            ),
            athlete_constraint_repository=(
                FakeAthleteConstraintRepository()
            ),
        )
    )

    from opencoach.coaching.manual_session_move_service import (
        ManualSessionMoveTargetUnavailableError,
    )

    with pytest.raises(
        ManualSessionMoveTargetUnavailableError,
        match="grosse séance",
    ):
        service.move(
            athlete_profile_id=(
                PROFILE_ID
            ),
            athlete=make_athlete(),
            session_id=session.id,
            target_date=date(
                2026,
                9,
                12,
            ),
            reference_date=date(
                2026,
                9,
                8,
            ),
        )

