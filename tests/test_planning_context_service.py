import pytest
from datetime import date
from uuid import uuid4

from opencoach.models import (
    AthleteConstraint,
    AthleteProfile,
    Race,
)
from opencoach.planning import PlanningContextService
from opencoach.readiness import (
    ReadinessDataUnavailableError,
)
from opencoach.training import (
    RecentTrainingLoad,
    TrainingStats,
)


PLANNING_DATE = date(
    2026,
    8,
    22,
)


def create_race(
    *,
    name: str,
    race_date: date,
    priority: str,
) -> Race:
    return Race(
        id=uuid4(),
        date=race_date,
        name=name,
        location="Test",
        race_type="trail",
        priority=priority,
        distance_km=42.0,
        elevation_gain_m=2000.0,
    )


class FakeProfileService:
    def __init__(
        self,
        profile: AthleteProfile,
    ) -> None:
        self.profile = profile

    def get_profile(self) -> AthleteProfile:
        return self.profile


class FakeRaceRepository:
    def __init__(
        self,
        *,
        primary_race: Race | None,
        training_races: list[Race],
    ) -> None:
        self.primary_race = primary_race
        self.training_races = training_races

    def get_next_primary_race(
        self,
        athlete_profile_id,
        from_date,
    ):
        return self.primary_race

    def list_training_races_before(
        self,
        athlete_profile_id,
        from_date,
        primary_date,
    ):
        return self.training_races

class FakeConstraintRepository:
    def __init__(
        self,
        constraints: list[AthleteConstraint],
    ) -> None:
        self.constraints = constraints

        self.start_date = None
        self.end_date = None

    def list_overlapping(
        self,
        athlete_profile_id,
        start_date,
        end_date,
    ):
        self.start_date = start_date
        self.end_date = end_date

        return self.constraints

class FakeReadinessService:
    def __init__(
        self,
        result=None,
        *,
        unavailable: bool = False,
    ) -> None:
        self.result = result
        self.unavailable = unavailable

    def calculate(
        self,
        athlete_profile_id,
        target_date,
    ):
        if self.unavailable:
            raise ReadinessDataUnavailableError(
                "Readiness indisponible."
            )

        return self.result


class FakeRecentLoadService:
    def __init__(
        self,
        result: RecentTrainingLoad,
    ) -> None:
        self.result = result
        self.requested_days = None

    def calculate(
        self,
        athlete_profile_id,
        target_date,
        *,
        days=7,
    ):
        self.requested_days = days
        return self.result


class FakeTrainingStatsService:
    def __init__(
        self,
        result: TrainingStats,
    ) -> None:
        self.result = result
        self.start_date = None
        self.end_date = None

    def calculate(
        self,
        athlete_profile_id,
        start_date,
        end_date,
    ):
        self.start_date = start_date
        self.end_date = end_date
        return self.result


def create_recent_load() -> RecentTrainingLoad:
    return RecentTrainingLoad(
        days=(),
        analyzed_days=0,
        planned_load_total=0.0,
        actual_load_total=0.0,
        above_plan_days=0,
        below_plan_days=0,
        on_plan_days=0,
        broken_rest_days=0,
        respected_rest_days=0,
    )


def create_stats() -> TrainingStats:
    return TrainingStats(
        start_date=date(
            2026,
            7,
            25,
        ),
        end_date=date(
            2026,
            8,
            21,
        ),
        activities_count=12,
        manual_sessions_count=0,
        total_duration_minutes=1260,
        total_distance_km=180.0,
        total_elevation_gain_m=6200.0,
        measured_load=750.0,
        estimated_load=0.0,
    )


def test_builds_complete_planning_context() -> None:
    athlete_profile_id = uuid4()

    athlete = AthleteProfile()

    primary_race = create_race(
        name="Objectif principal",
        race_date=date(
            2026,
            10,
            18,
        ),
        priority="primary",
    )

    training_race = create_race(
        name="Course préparatoire",
        race_date=date(
            2026,
            9,
            20,
        ),
        priority="training",
    )
    constraint = create_constraint()

    constraint_repository = FakeConstraintRepository(
        [constraint]
    )
    recent_load = create_recent_load()
    stats = create_stats()

    recent_load_service = FakeRecentLoadService(
        recent_load
    )

    stats_service = FakeTrainingStatsService(
        stats
    )

    service = PlanningContextService(
        profile_service=FakeProfileService(
            athlete
        ),
        race_repository=FakeRaceRepository(
            primary_race=primary_race,
            training_races=[training_race],
        ),
        readiness_service=FakeReadinessService(
            result=None
        ),
        recent_load_service=recent_load_service,
        training_stats_service=stats_service,
        constraint_repository=constraint_repository,
    )

    context = service.build(
        athlete_profile_id,
        PLANNING_DATE,
    )

    assert context.planning_date == PLANNING_DATE
    assert context.athlete is athlete

    assert context.primary_race is primary_race

    assert context.training_races == (
        training_race,
    )

    assert context.recent_load is recent_load
    assert context.recent_stats is stats

    assert recent_load_service.requested_days == 7

    assert stats_service.start_date == date(
        2026,
        7,
        25,
    )

    assert stats_service.end_date == date(
        2026,
        8,
        21,
    )

    assert context.constraints == (
        constraint,
    )

    assert context.constraints_end_date == date(
        2026,
        9,
        4,
    )

    assert constraint_repository.start_date == (
        PLANNING_DATE
    )

    assert constraint_repository.end_date == date(
        2026,
        9,
        4,
    )


def test_builds_context_without_primary_race() -> None:
    service = PlanningContextService(
        profile_service=FakeProfileService(
            AthleteProfile()
        ),
        race_repository=FakeRaceRepository(
            primary_race=None,
            training_races=[],
        ),
        readiness_service=FakeReadinessService(),
        recent_load_service=FakeRecentLoadService(
            create_recent_load()
        ),
        training_stats_service=FakeTrainingStatsService(
            create_stats()
        ),
        constraint_repository=FakeConstraintRepository(
            []
        ),
    )

    context = service.build(
        uuid4(),
        PLANNING_DATE,
    )

    assert context.primary_race is None
    assert context.training_races == ()


def test_builds_context_when_readiness_is_unavailable() -> None:
    service = PlanningContextService(
        profile_service=FakeProfileService(
            AthleteProfile()
        ),
        race_repository=FakeRaceRepository(
            primary_race=None,
            training_races=[],
        ),
        readiness_service=FakeReadinessService(),
        recent_load_service=FakeRecentLoadService(
            create_recent_load()
        ),
        training_stats_service=FakeTrainingStatsService(
            create_stats()
        ),
        constraint_repository=FakeConstraintRepository(
            []
        ),
    )

    context = service.build(
        uuid4(),
        PLANNING_DATE,
    )

    assert context.readiness is None

def create_constraint() -> AthleteConstraint:
    return AthleteConstraint(
        id=uuid4(),
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
        constraint_type="work",
        availability="unavailable",
    )

def test_constraint_horizon_can_be_configured() -> None:
    constraint_repository = FakeConstraintRepository(
        []
    )

    service = PlanningContextService(
        profile_service=FakeProfileService(
            AthleteProfile()
        ),
        race_repository=FakeRaceRepository(
            primary_race=None,
            training_races=[],
        ),
        readiness_service=FakeReadinessService(),
        recent_load_service=FakeRecentLoadService(
            create_recent_load()
        ),
        training_stats_service=FakeTrainingStatsService(
            create_stats()
        ),
        constraint_repository=constraint_repository,
    )

    context = service.build(
        uuid4(),
        PLANNING_DATE,
        constraint_days=7,
    )

    assert context.constraints_end_date == date(
        2026,
        8,
        28,
    )

    assert constraint_repository.start_date == (
        PLANNING_DATE
    )

    assert constraint_repository.end_date == date(
        2026,
        8,
        28,
    )

def test_rejects_invalid_constraint_horizon() -> None:
    service = PlanningContextService(
        profile_service=FakeProfileService(
            AthleteProfile()
        ),
        race_repository=FakeRaceRepository(
            primary_race=None,
            training_races=[],
        ),
        readiness_service=FakeReadinessService(),
        recent_load_service=FakeRecentLoadService(
            create_recent_load()
        ),
        training_stats_service=FakeTrainingStatsService(
            create_stats()
        ),
        constraint_repository=FakeConstraintRepository(
            []
        ),
    )

    with pytest.raises(
        ValueError,
        match="contraintes",
    ):
        service.build(
            uuid4(),
            PLANNING_DATE,
            constraint_days=0,
        )