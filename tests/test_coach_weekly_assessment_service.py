from datetime import date, datetime, timedelta
from uuid import UUID, uuid4

from opencoach.coaching.weekly_assessment import (
    CoachHistoryConfidenceLevel,
    CoachWeeklyStatus,
)
from opencoach.coaching.weekly_assessment_service import (
    CoachWeeklyAssessmentService,
)
from opencoach.models import Activity
from opencoach.planning.history.training import (
    TrainingHistorySnapshot,
)
from opencoach.training import TrainingStats
from opencoach.training.weekly_load_projection import (
    WeeklyLoadProjection,
)


REFERENCE_DATE = date(
    2026,
    8,
    27,
)


class FakeWeeklyLoadProjectionService:
    def __init__(
        self,
        projection: WeeklyLoadProjection,
    ) -> None:
        self.projection = projection

        self.calls: list[
            tuple[
                UUID,
                date,
            ]
        ] = []

    def calculate(
        self,
        athlete_profile_id: UUID,
        reference_date: date,
    ) -> WeeklyLoadProjection:
        self.calls.append(
            (
                athlete_profile_id,
                reference_date,
            )
        )

        return self.projection


class FakeTrainingHistorySnapshotService:
    def __init__(
        self,
        snapshot: TrainingHistorySnapshot,
    ) -> None:
        self.snapshot = snapshot

        self.calls: list[
            tuple[
                UUID,
                date,
            ]
        ] = []

    def build(
        self,
        athlete_profile_id: UUID,
        reference_date: date,
    ) -> TrainingHistorySnapshot:
        self.calls.append(
            (
                athlete_profile_id,
                reference_date,
            )
        )

        return self.snapshot


def create_stats(
    *,
    days: int,
    duration_minutes: int,
    training_load: float,
    sessions_count: int,
) -> TrainingStats:
    return TrainingStats(
        start_date=(
            REFERENCE_DATE
            - timedelta(days=days)
        ),
        end_date=(
            REFERENCE_DATE
            - timedelta(days=1)
        ),
        activities_count=sessions_count,
        manual_sessions_count=0,
        total_duration_minutes=(
            duration_minutes
        ),
        total_distance_km=44.48,
        total_elevation_gain_m=279.4,
        measured_load=training_load,
        estimated_load=0.0,
    )


def create_activity() -> Activity:
    return Activity(
        provider="test",
        provider_activity_id="activity-1",
        name="Course",
        sport_type="Run",
        start_at=datetime(
            2026,
            8,
            21,
            8,
            0,
        ),
        moving_time_seconds=3600,
        training_load=50.0,
    )


def create_snapshot() -> TrainingHistorySnapshot:
    stats_7 = create_stats(
        days=7,
        duration_minutes=256,
        training_load=233.0,
        sessions_count=4,
    )

    stats_14 = create_stats(
        days=14,
        duration_minutes=256,
        training_load=233.0,
        sessions_count=4,
    )

    stats_21 = create_stats(
        days=21,
        duration_minutes=256,
        training_load=233.0,
        sessions_count=4,
    )

    stats_28 = create_stats(
        days=28,
        duration_minutes=256,
        training_load=233.0,
        sessions_count=4,
    )

    return TrainingHistorySnapshot(
        reference_date=REFERENCE_DATE,
        last_7_days=stats_7,
        last_14_days=stats_14,
        last_21_days=stats_21,
        last_28_days=stats_28,
        last_42_days=stats_28,
        last_84_days=stats_28,
        activities_84_days=(
            create_activity(),
        ),
    )


def create_projection() -> WeeklyLoadProjection:
    return WeeklyLoadProjection(
        week_start=date(
            2026,
            8,
            24,
        ),
        week_end=date(
            2026,
            8,
            30,
        ),
        as_of_date=REFERENCE_DATE,

        actual_load_to_date=72.0,
        remaining_planned_load=79.5,
        projected_week_load=151.5,

        target_load=152.95,
        load_min=145.30,
        load_max=160.60,

        projected_gap=-1.45,
        projected_gap_percent=-0.9,

        remaining_days=3,

        adaptation_opportunity=False,
        adaptation_direction=None,

        completed_sessions_count=0,
        missed_sessions_count=1,
        remaining_sessions_count=4,
        planned_sessions_count=5,
        supplementary_sessions_count=1,
    )


def test_service_builds_complete_weekly_assessment() -> None:
    athlete_profile_id = uuid4()

    projection_service = (
        FakeWeeklyLoadProjectionService(
            create_projection()
        )
    )

    history_service = (
        FakeTrainingHistorySnapshotService(
            create_snapshot()
        )
    )

    service = (
        CoachWeeklyAssessmentService(
            weekly_load_projection_service=(
                projection_service
            ),
            training_history_service=(
                history_service
            ),
        )
    )

    result = service.calculate(
        athlete_profile_id,
        REFERENCE_DATE,
    )

    assert (
        result.status
        is CoachWeeklyStatus.ALIGNED
    )

    assert result.target_load == 152.95
    assert result.projected_week_load == 151.5
    assert result.projected_gap_percent == -0.9

    assert result.history_window_days == 7

    assert result.history_confidence == 0.25

    assert (
        result.history_confidence_level
        is CoachHistoryConfidenceLevel.LOW
    )

    assert (
        result.adaptation_opportunity
        is False
    )

    assert (
        projection_service.calls
        == [
            (
                athlete_profile_id,
                REFERENCE_DATE,
            )
        ]
    )

    assert (
        history_service.calls
        == [
            (
                athlete_profile_id,
                REFERENCE_DATE,
            )
        ]
    )


def test_service_exposes_weekly_context_for_coach_text() -> None:
    service = (
        CoachWeeklyAssessmentService(
            weekly_load_projection_service=(
                FakeWeeklyLoadProjectionService(
                    create_projection()
                )
            ),
            training_history_service=(
                FakeTrainingHistorySnapshotService(
                    create_snapshot()
                )
            ),
        )
    )

    result = service.calculate(
        uuid4(),
        REFERENCE_DATE,
    )

    assert (
        "trajectoire"
        in result.headline.lower()
    )

    assert (
        "0.9 %"
        in result.analysis
    )

    assert (
        "1 semaine"
        in result.analysis
    )

    assert (
        "Conservez le programme prévu"
        in result.instruction
    )
