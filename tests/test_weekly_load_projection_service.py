from datetime import date
from uuid import UUID, uuid4

from opencoach.database.repositories import (
    TrainingSessionRepository,
)
from opencoach.models import (
    Activity,
    TrainingSession,
    WeeklyTrainingPlan,
)
from opencoach.training import (
    DailyTrainingLoad,
    WeeklyLoadProjectionService,
)


TARGET_DATE = date(
    2026,
    8,
    27,
)


class FakeTrainingSessionRepository(
    TrainingSessionRepository,
):
    def __init__(
        self,
        sessions: list[TrainingSession],
    ) -> None:
        self.sessions = sessions

    def save_session(
        self,
        athlete_profile_id: UUID,
        session: TrainingSession,
    ) -> TrainingSession:
        self.sessions.append(session)
        return session

    def get_session(
        self,
        athlete_profile_id: UUID,
        session_id: UUID,
    ) -> TrainingSession | None:
        for session in self.sessions:
            if session.id == session_id:
                return session

        return None

    def list_sessions_between(
        self,
        athlete_profile_id: UUID,
        start_date: date,
        end_date: date,
    ) -> list[TrainingSession]:
        return [
            session
            for session in self.sessions
            if (
                start_date
                <= session.date
                <= end_date
            )
        ]

    def update_status(
        self,
        athlete_profile_id: UUID,
        session_id: UUID,
        status: str,
    ) -> TrainingSession:
        session = self.get_session(
            athlete_profile_id,
            session_id,
        )

        if session is None:
            raise RuntimeError(
                "Session introuvable."
            )

        session.status = status
        return session

    def link_activity(
        self,
        athlete_profile_id: UUID,
        session_id: UUID,
        activity_id: UUID | None,
    ) -> TrainingSession:
        session = self.get_session(
            athlete_profile_id,
            session_id,
        )

        if session is None:
            raise RuntimeError(
                "Session introuvable."
            )

        session.activity_id = activity_id
        return session

    def list_candidate_activities_for_date(
        self,
        athlete_profile_id: UUID,
        session_date: date,
    ) -> list[Activity]:
        return []

    def list_unlinked_activities_for_date(
        self,
        athlete_profile_id: UUID,
        session_date: date,
    ) -> list[Activity]:
        return []

    def delete_session(
        self,
        session_id,
    ) -> None:
        self.sessions = [
            session
            for session in self.sessions
            if session.id != session_id
        ]


class FakeWeeklyTrainingPlanRepository:
    def __init__(
        self,
        plan: WeeklyTrainingPlan | None = None,
    ) -> None:
        self.plan = plan

    def save_plan(
        self,
        plan: WeeklyTrainingPlan,
    ) -> WeeklyTrainingPlan:
        self.plan = plan
        return plan

    def get_plan_for_week(
        self,
        athlete_profile_id: UUID,
        week_start: date,
    ) -> WeeklyTrainingPlan | None:
        if self.plan is None:
            return None

        if (
            self.plan.athlete_profile_id
            != athlete_profile_id
        ):
            return None

        if (
            self.plan.week_start
            != week_start
        ):
            return None

        return self.plan


class FakeDailyTrainingLoadService:
    def __init__(
        self,
        loads: dict[
            date,
            float,
        ],
    ) -> None:
        self.loads = loads

    def calculate(
        self,
        athlete_profile_id: UUID,
        target_date: date,
    ) -> DailyTrainingLoad:
        load = self.loads.get(
            target_date,
            0.0,
        )

        return DailyTrainingLoad(
            date=target_date,
            activities_count=(
                1
                if load > 0
                else 0
            ),
            manual_sessions_count=0,
            total_duration_minutes=0,
            total_distance_km=0.0,
            total_elevation_gain_m=0.0,
            measured_load=load,
            estimated_load=0.0,
            sport_types=(
                ("Run",)
                if load > 0
                else ()
            ),
        )


def create_session(
    *,
    session_date: date,
    session_type: str = "aerobic_easy",
    sport_type: str = "Run",
    duration_minutes: int = 60,
    intensity: str = "easy",
    status: str = "planned",
    planning_key: str | None = "week:test",
) -> TrainingSession:
    return TrainingSession(
        id=uuid4(),
        date=session_date,
        type=session_type,
        sport_type=sport_type,
        title="Séance test",
        description="",
        duration_minutes=duration_minutes,
        distance_km=None,
        elevation_gain_m=None,
        intensity=intensity,
        heart_rate_zone=None,
        status=status,
        activity_id=None,
        planning_key=planning_key,
    )


def create_service(
    *,
    sessions: list[TrainingSession],
    loads: dict[
        date,
        float,
    ],
    target_load: float | None = None,
) -> WeeklyLoadProjectionService:
    athlete_profile_id = uuid4()

    plan = None

    if target_load is not None:
        plan = WeeklyTrainingPlan(
            id=None,
            athlete_profile_id=(
                athlete_profile_id
            ),
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
            phase="base",
            phase_week_index=1,
            target_load=target_load,
            load_min=(
                target_load * 0.95
            ),
            load_max=(
                target_load * 1.05
            ),
            reference_duration_minutes=240.0,
            target_duration_minutes=240.0,
            long_endurance_reference_minutes=90.0,
            schedule_pressure="normal",
            athlete_schedule_constrained=False,
        )

    service = WeeklyLoadProjectionService(
        training_session_repository=(
            FakeTrainingSessionRepository(
                sessions
            )
        ),
        daily_training_load_service=(
            FakeDailyTrainingLoadService(
                loads
            )
        ),
        weekly_training_plan_repository=(
            FakeWeeklyTrainingPlanRepository(
                plan
            )
        ),
    )

    service._test_athlete_profile_id = (
        athlete_profile_id
    )

    return service


def test_weekly_projection_combines_actual_and_remaining_plan() -> None:
    service = create_service(
        sessions=[
            create_session(
                session_date=date(
                    2026,
                    8,
                    25,
                ),
                status="completed",
            ),
            create_session(
                session_date=TARGET_DATE,
                duration_minutes=45,
                status="planned",
            ),
            create_session(
                session_date=date(
                    2026,
                    8,
                    30,
                ),
                session_type="long_endurance",
                duration_minutes=60,
                status="planned",
            ),
        ],
        loads={
            date(
                2026,
                8,
                25,
            ): 40.0,
            date(
                2026,
                8,
                26,
            ): 55.0,
        },
    )

    result = service.calculate(
        service._test_athlete_profile_id,
        TARGET_DATE,
    )

    assert result.actual_load_to_date == 95.0
    assert result.remaining_planned_load > 0.0

    assert (
        result.projected_week_load
        == (
            result.actual_load_to_date
            + result.remaining_planned_load
        )
    )

    assert result.completed_sessions_count == 1
    assert result.remaining_sessions_count == 2


def test_weekly_projection_counts_missed_session() -> None:
    service = create_service(
        sessions=[
            create_session(
                session_date=date(
                    2026,
                    8,
                    25,
                ),
                status="planned",
            ),
        ],
        loads={},
    )

    result = service.calculate(
        service._test_athlete_profile_id,
        TARGET_DATE,
    )

    assert result.missed_sessions_count == 1
    assert result.completed_sessions_count == 0


def test_weekly_projection_counts_supplementary_without_prescribing_it() -> None:
    service = create_service(
        sessions=[
            create_session(
                session_date=date(
                    2026,
                    8,
                    26,
                ),
                session_type="supplementary",
                status="completed",
                planning_key=None,
            ),
        ],
        loads={
            date(
                2026,
                8,
                26,
            ): 45.0,
        },
    )

    result = service.calculate(
        service._test_athlete_profile_id,
        TARGET_DATE,
    )

    assert result.actual_load_to_date == 45.0
    assert result.supplementary_sessions_count == 1
    assert result.planned_sessions_count == 0
    assert result.remaining_planned_load == 0.0


def test_weekly_projection_supports_multiple_sessions_same_day() -> None:
    service = create_service(
        sessions=[
            create_session(
                session_date=TARGET_DATE,
                session_type="aerobic_easy",
                duration_minutes=45,
                status="planned",
            ),
            create_session(
                session_date=TARGET_DATE,
                session_type="strength_lower_body",
                sport_type="Strength",
                duration_minutes=15,
                intensity="hard",
                status="planned",
            ),
        ],
        loads={},
    )

    result = service.calculate(
        service._test_athlete_profile_id,
        TARGET_DATE,
    )

    assert result.remaining_sessions_count == 2
    assert result.planned_sessions_count == 2
    assert result.remaining_planned_load > 0.0


def test_weekly_projection_without_generated_plan_has_no_week_plan() -> None:
    service = create_service(
        sessions=[
            create_session(
                session_date=date(
                    2026,
                    8,
                    26,
                ),
                session_type="threshold",
                status="planned",
                planning_key=None,
            ),
        ],
        loads={
            date(
                2026,
                8,
                26,
            ): 30.0,
        },
    )

    result = service.calculate(
        service._test_athlete_profile_id,
        TARGET_DATE,
    )

    assert result.has_week_plan is False
    assert result.planned_sessions_count == 0
    assert result.remaining_sessions_count == 0



def test_weekly_projection_detects_under_target_adaptation() -> None:
    service = create_service(
        sessions=[],
        loads={
            date(
                2026,
                8,
                26,
            ): 100.0,
        },
        target_load=200.0,
    )

    result = service.calculate(
        service._test_athlete_profile_id,
        TARGET_DATE,
    )

    assert result.target_load == 200.0
    assert result.projected_week_load == 100.0
    assert result.projected_gap == -100.0
    assert result.projected_gap_percent == -50.0

    assert result.adaptation_opportunity is True
    assert result.adaptation_direction == "increase"

    assert result.remaining_days == 3


def test_weekly_projection_inside_tolerance_needs_no_adaptation() -> None:
    service = create_service(
        sessions=[],
        loads={
            date(
                2026,
                8,
                26,
            ): 180.0,
        },
        target_load=200.0,
    )

    result = service.calculate(
        service._test_athlete_profile_id,
        TARGET_DATE,
    )

    assert result.projected_gap_percent == -10.0
    assert result.adaptation_opportunity is False
    assert result.adaptation_direction is None


def test_weekly_projection_detects_over_target_adaptation() -> None:
    service = create_service(
        sessions=[],
        loads={
            date(
                2026,
                8,
                26,
            ): 240.0,
        },
        target_load=200.0,
    )

    result = service.calculate(
        service._test_athlete_profile_id,
        TARGET_DATE,
    )

    assert result.projected_gap_percent == 20.0
    assert result.adaptation_opportunity is True
    assert result.adaptation_direction == "reduce"


def test_weekly_projection_without_target_has_no_adaptation() -> None:
    service = create_service(
        sessions=[],
        loads={
            date(
                2026,
                8,
                26,
            ): 100.0,
        },
    )

    result = service.calculate(
        service._test_athlete_profile_id,
        TARGET_DATE,
    )

    assert result.target_load is None
    assert result.projected_gap is None
    assert result.projected_gap_percent is None
    assert result.adaptation_opportunity is False
    assert result.adaptation_direction is None
