from datetime import date, datetime
from uuid import uuid4

import pytest

from opencoach.models import (
    Activity,
    ActivityDetail,
    ActivityStreams,
    TrainingSession,
)
from opencoach.training.session_execution.persisted_analysis import (
    PersistedSessionExecutionAnalysis,
)
from opencoach.training.session_execution.validation_service import (
    TrainingSessionActivityNotFoundError,
    TrainingSessionAlreadyValidatedError,
    TrainingSessionInvalidPrescriptionError,
    TrainingSessionMissingActivityDetailError,
    TrainingSessionNotFoundError,
    ValidateTrainingSessionService,
)


class FakeTrainingSessionRepository:
    def __init__(self, session):
        self.session = session
        self.saved = None

    def get_session(
        self,
        athlete_profile_id,
        session_id,
    ):
        if (
            self.session is not None
            and self.session.id == session_id
        ):
            return self.session

        return None

    def save_session(
        self,
        athlete_profile_id,
        session,
    ):
        self.saved = session
        self.session = session
        return session


class FakeActivityRepository:
    def __init__(self, activity):
        self.activity = activity

    def get_activity(
        self,
        athlete_profile_id,
        activity_id,
    ):
        if (
            self.activity is not None
            and self.activity.id == activity_id
        ):
            return self.activity

        return None


class FakeActivityDetailRepository:
    def __init__(self, detail):
        self.detail = detail

    def get_activity_detail(
        self,
        athlete_profile_id,
        activity_id,
    ):
        return self.detail


class FakeValidationWriter:
    def __init__(self):
        self.assessment = None
        self.persisted_session = None

    def persist(
        self,
        *,
        athlete_profile_id,
        session,
        assessment,
    ):
        self.assessment = assessment
        self.persisted_session = session

        analysis = PersistedSessionExecutionAnalysis(
            id=uuid4(),
            athlete_profile_id=(
                athlete_profile_id
            ),
            training_session_id=(
                assessment.session_id
            ),
            activity_id=(
                assessment.activity_id
            ),
            goal_type=(
                assessment.goal_analysis
                .goal_type.value
            ),
            overall_status=(
                assessment.overall_status.value
            ),
            technical_status=(
                assessment.technical_status.value
                if assessment.technical_status
                else None
            ),
            objective=(
                assessment.goal_analysis.objective
            ),
            metrics=(),
            strengths=(),
            attention_points=(),
            debriefing=(
                assessment.goal_analysis.debriefing
            ),
            derived_results=(),
            analyzed_at=datetime.now(),
        )

        return (
            session,
            analysis,
        )


def session():
    return TrainingSession(
        id=uuid4(),
        date=date(2026, 8, 29),
        type="aerobic_easy",
        sport_type="Run",
        title="Endurance facile",
        description="EF",
        duration_minutes=45,
        planning_key="2026-08-29:aerobic_easy",
        intensity="easy",
        prescription={
            "version": 1,
            "blocks": [],
            "work_structure": {
                "type": "continuous",
                "stimulus": "aerobic_easy",
                "available_minutes": 45,
                "continuous_minutes": 45,
                "description": "Endurance facile.",
                "circuit": None,
                "intervals": [],
            },
            "intensity": {
                "targets": [
                    {
                        "reference": "heart_rate",
                        "minimum": 129,
                        "maximum": 152,
                        "unit": "bpm",
                        "label": "Zone EF",
                    },
                ],
                "guidance": [],
            },
        },
        status="planned",
    )


def activity():
    return Activity(
        id=uuid4(),
        provider="intervals_icu",
        provider_activity_id="i-test",
        start_at=datetime(
            2026,
            8,
            29,
            8,
            0,
        ),
        sport_type="Run",
        name="Course",
        moving_time_seconds=2700,
        elapsed_time_seconds=2700,
        distance_m=7000,
        average_heart_rate=145,
        max_heart_rate=155,
    )


def detail(activity_value):
    return ActivityDetail(
        provider_activity_id=(
            activity_value.provider_activity_id
        ),
        streams=ActivityStreams(),
    )


def service(
    *,
    session_value=None,
    activity_value=None,
    detail_value=None,
):
    session_value = (
        session()
        if session_value is None
        else session_value
    )

    activity_value = (
        activity()
        if activity_value is None
        else activity_value
    )

    if detail_value is None:
        detail_value = detail(
            activity_value
        )

    return (
        ValidateTrainingSessionService(
            training_session_repository=(
                FakeTrainingSessionRepository(
                    session_value
                )
            ),
            activity_repository=(
                FakeActivityRepository(
                    activity_value
                )
            ),
            activity_detail_repository=(
                FakeActivityDetailRepository(
                    detail_value
                )
            ),
            validation_writer=(
                FakeValidationWriter()
            ),
        ),
        session_value,
        activity_value,
    )


def test_athlete_selected_activity_is_validated() -> None:
    application, planned, performed = service()

    result = application.execute(
        athlete_profile_id=uuid4(),
        training_session_id=planned.id,
        activity_id=performed.id,
    )

    assert result.session.status == "completed"

    assert (
        result.session.activity_id
        == performed.id
    )

    assert (
        result.analysis.training_session_id
        == planned.id
    )

    assert (
        result.analysis.activity_id
        == performed.id
    )


def test_service_never_selects_an_activity_itself() -> None:
    application, planned, _ = service()

    unknown_activity_id = uuid4()

    with pytest.raises(
        TrainingSessionActivityNotFoundError
    ):
        application.execute(
            athlete_profile_id=uuid4(),
            training_session_id=planned.id,
            activity_id=unknown_activity_id,
        )


def test_missing_session_is_rejected() -> None:
    application, _, performed = service(
        session_value=None,
    )

    application.training_session_repository.session = None

    with pytest.raises(
        TrainingSessionNotFoundError
    ):
        application.execute(
            athlete_profile_id=uuid4(),
            training_session_id=uuid4(),
            activity_id=performed.id,
        )


def test_completed_session_cannot_be_validated_again() -> None:
    planned = session()
    planned.status = "completed"

    application, _, performed = service(
        session_value=planned,
    )

    with pytest.raises(
        TrainingSessionAlreadyValidatedError
    ):
        application.execute(
            athlete_profile_id=uuid4(),
            training_session_id=planned.id,
            activity_id=performed.id,
        )


def test_missing_activity_detail_prevents_validation() -> None:
    planned = session()
    performed = activity()

    application, _, _ = service(
        session_value=planned,
        activity_value=performed,
        detail_value=None,
    )

    application.activity_detail_repository.detail = None

    with pytest.raises(
        TrainingSessionMissingActivityDetailError
    ):
        application.execute(
            athlete_profile_id=uuid4(),
            training_session_id=planned.id,
            activity_id=performed.id,
        )

    assert (
        application.validation_writer.persisted_session
        is None
    )


def test_invalid_prescription_prevents_validation() -> None:
    planned = session()
    planned.prescription = None

    application, _, performed = service(
        session_value=planned,
    )

    with pytest.raises(
        TrainingSessionInvalidPrescriptionError
    ):
        application.execute(
            athlete_profile_id=uuid4(),
            training_session_id=planned.id,
            activity_id=performed.id,
        )

    assert (
        application.validation_writer.persisted_session
        is None
    )
