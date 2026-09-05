from __future__ import annotations

from datetime import date
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from opencoach.api.coaching.dependencies import (
    build_weekly_debrief_application_service,
)
from opencoach.coaching.weekly_debrief import (
    WeeklyDebriefFacts,
    build_weekly_debrief,
)
from opencoach.database import models  # noqa: F401
from opencoach.database.base import Base
from opencoach.database.models import (
    AthleteProfile,
    User,
)
from opencoach.database.repositories.sql_weekly_debrief import (
    SqlWeeklyDebriefRepository,
)


WEEK_START = date(2026, 8, 31)
WEEK_END = date(2026, 9, 6)


@pytest.fixture
def session() -> Session:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
    )

    Base.metadata.create_all(engine)

    with Session(engine) as database:
        yield database

    Base.metadata.drop_all(engine)
    engine.dispose()


def create_facts(
    *,
    completed_sessions: int,
    actual_load: float,
) -> WeeklyDebriefFacts:
    return WeeklyDebriefFacts(
        week_start=WEEK_START,
        week_end=WEEK_END,
        planned_sessions=5,
        completed_sessions=completed_sessions,
        skipped_sessions=5 - completed_sessions,
        supplementary_sessions=0,
        planned_duration_minutes=300,
        actual_duration_minutes=(
            completed_sessions * 60
        ),
        planned_load=300.0,
        actual_load=actual_load,
        key_sessions_planned=2,
        key_sessions_completed=min(
            completed_sessions,
            2,
        ),
        compliant_intensity_sessions=(
            completed_sessions
        ),
        analyzed_intensity_sessions=(
            completed_sessions
        ),
        history_confidence=1.0,
    )


def test_two_profiles_keep_owner_and_debrief_isolation(
    session: Session,
) -> None:
    user_a = User(
        id=uuid4(),
        email="weekly-a@example.test",
    )
    user_b = User(
        id=uuid4(),
        email="weekly-b@example.test",
    )

    athlete_a = AthleteProfile(
        id=uuid4(),
        user_id=user_a.id,
        first_name="Athlete",
        last_name="A",
    )
    athlete_b = AthleteProfile(
        id=uuid4(),
        user_id=user_b.id,
        first_name="Athlete",
        last_name="B",
    )

    session.add_all(
        [
            user_a,
            user_b,
            athlete_a,
            athlete_b,
        ]
    )
    session.commit()

    # ---------------------------------------------------------
    # 1. Relation SQL athlete -> propriétaire
    # ---------------------------------------------------------

    owner_a = session.scalar(
        select(AthleteProfile.user_id).where(
            AthleteProfile.id == athlete_a.id
        )
    )
    owner_b = session.scalar(
        select(AthleteProfile.user_id).where(
            AthleteProfile.id == athlete_b.id
        )
    )

    assert owner_a == user_a.id
    assert owner_b == user_b.id

    assert owner_a != owner_b
    assert athlete_a.id != athlete_b.id

    # ---------------------------------------------------------
    # 2. Même semaine, deux débriefs distincts
    # ---------------------------------------------------------

    repository = SqlWeeklyDebriefRepository(
        session
    )

    facts_a = create_facts(
        completed_sessions=5,
        actual_load=305.0,
    )
    facts_b = create_facts(
        completed_sessions=3,
        actual_load=180.0,
    )

    debrief_a = build_weekly_debrief(
        facts_a
    )
    debrief_b = build_weekly_debrief(
        facts_b
    )

    stored_a = repository.save_closed(
        athlete_a.id,
        facts_a,
        debrief_a,
        adaptation_payload={
            "profile": "A",
        },
    )

    stored_b = repository.save_closed(
        athlete_b.id,
        facts_b,
        debrief_b,
        adaptation_payload={
            "profile": "B",
        },
    )

    assert stored_a.id != stored_b.id

    assert (
        stored_a.athlete_profile_id
        == athlete_a.id
    )
    assert (
        stored_b.athlete_profile_id
        == athlete_b.id
    )

    assert (
        stored_a.facts.week_start
        == WEEK_START
    )
    assert (
        stored_b.facts.week_start
        == WEEK_START
    )

    # ---------------------------------------------------------
    # 3. Lecture strictement scoped
    # ---------------------------------------------------------

    loaded_a = repository.get_for_week(
        athlete_a.id,
        WEEK_START,
    )
    loaded_b = repository.get_for_week(
        athlete_b.id,
        WEEK_START,
    )

    assert loaded_a is not None
    assert loaded_b is not None

    assert (
        loaded_a.athlete_profile_id
        == athlete_a.id
    )
    assert (
        loaded_b.athlete_profile_id
        == athlete_b.id
    )

    assert loaded_a.id == stored_a.id
    assert loaded_b.id == stored_b.id

    assert loaded_a.id != loaded_b.id

    assert loaded_a.adaptation_payload == {
        "profile": "A",
    }
    assert loaded_b.adaptation_payload == {
        "profile": "B",
    }

    assert loaded_a.facts == facts_a
    assert loaded_b.facts == facts_b


def test_composition_factories_are_scoped_by_profile(
    session: Session,
) -> None:
    user_a = User(
        id=uuid4(),
        email="factory-a@example.test",
    )
    user_b = User(
        id=uuid4(),
        email="factory-b@example.test",
    )

    athlete_a = AthleteProfile(
        id=uuid4(),
        user_id=user_a.id,
        first_name="Factory",
        last_name="A",
    )
    athlete_b = AthleteProfile(
        id=uuid4(),
        user_id=user_b.id,
        first_name="Factory",
        last_name="B",
    )

    session.add_all(
        [
            user_a,
            user_b,
            athlete_a,
            athlete_b,
        ]
    )
    session.commit()

    context_factory_calls: list[UUID] = []
    planning_factory_calls: list[UUID] = []

    class ContextResolver:
        def resolve(
            self,
            *,
            athlete_profile_id,
            reference_date,
            runtime_facts,
        ):
            raise AssertionError(
                "resolve() ne doit pas être nécessaire "
                "dans ce test de composition."
            )

    class PlanningService:
        def execute(self, **kwargs):
            raise AssertionError(
                "execute() ne doit pas être nécessaire "
                "dans ce test de composition."
            )

    resolvers: dict[UUID, ContextResolver] = {}
    planners: dict[UUID, PlanningService] = {}

    def planning_context_factory(
        athlete_profile_id: UUID,
    ):
        context_factory_calls.append(
            athlete_profile_id
        )

        owner_id = session.scalar(
            select(
                AthleteProfile.user_id
            ).where(
                AthleteProfile.id
                == athlete_profile_id
            )
        )

        assert owner_id is not None

        resolver = ContextResolver()
        resolvers[athlete_profile_id] = resolver

        return resolver

    def planning_service_factory(
        athlete_profile_id: UUID,
    ):
        planning_factory_calls.append(
            athlete_profile_id
        )

        owner_id = session.scalar(
            select(
                AthleteProfile.user_id
            ).where(
                AthleteProfile.id
                == athlete_profile_id
            )
        )

        assert owner_id is not None

        planner = PlanningService()
        planners[athlete_profile_id] = planner

        return planner

    service = build_weekly_debrief_application_service(
        session,
        planning_context_factory=(
            planning_context_factory
        ),
        planning_service_factory=(
            planning_service_factory
        ),
    )

    context_a = service._planning_context_factory(
        athlete_a.id
    )
    context_b = service._planning_context_factory(
        athlete_b.id
    )

    planning_application = (
        service
        ._orchestrator
        ._planning_application_service
    )

    planner_a = (
        planning_application
        ._planning_service_factory(
            athlete_a.id
        )
    )
    planner_b = (
        planning_application
        ._planning_service_factory(
            athlete_b.id
        )
    )

    assert context_factory_calls == [
        athlete_a.id,
        athlete_b.id,
    ]

    assert planning_factory_calls == [
        athlete_a.id,
        athlete_b.id,
    ]

    assert context_a is resolvers[
        athlete_a.id
    ]
    assert context_b is resolvers[
        athlete_b.id
    ]

    assert planner_a is planners[
        athlete_a.id
    ]
    assert planner_b is planners[
        athlete_b.id
    ]

    assert context_a is not context_b
    assert planner_a is not planner_b



def _create_sql_profiles(
    session: Session,
    count: int = 3,
):
    users = []
    athletes = []

    for index in range(count):
        suffix = chr(
            ord("A") + index
        )

        user = User(
            id=uuid4(),
            email=(
                f"default-factory-{suffix.lower()}"
                "@example.test"
            ),
        )

        athlete = AthleteProfile(
            id=uuid4(),
            user_id=user.id,
            first_name="Default",
            last_name=suffix,
        )

        users.append(user)
        athletes.append(athlete)

    session.add_all(
        [
            *users,
            *athletes,
        ]
    )
    session.commit()

    return (
        tuple(users),
        tuple(athletes),
    )


def test_default_composition_factories_resolve_real_profile_owners(
    session: Session,
    monkeypatch,
) -> None:
    """Les factories par défaut doivent recevoir le vrai owner SQL."""

    import opencoach.api.coaching.dependencies as dependencies

    users, athletes = _create_sql_profiles(
        session
    )

    context_user_ids = []
    generation_user_ids = []

    class FakePreparedContext:
        planning_input = object()
        sport_disciplines = ()

    class FakeContextBuilder:
        def build(
            self,
            *,
            athlete_profile_id,
            planning_date,
            trajectory_start_date,
        ):
            return FakePreparedContext()

    def fake_get_planning_context_service(
        *,
        user_id,
        db,
        readiness_service,
        training_stats_service,
    ):
        assert db is session

        context_user_ids.append(
            user_id
        )

        return object()

    def fake_get_weekly_planning_context_builder(
        *,
        planning_context_service,
        history_service,
    ):
        assert planning_context_service is not None
        assert history_service is not None

        return FakeContextBuilder()

    def fake_get_athlete_generation_service(
        *,
        user_id,
        db,
        physiology_service,
        generation_service,
    ):
        assert db is session

        generation_user_ids.append(
            user_id
        )

        return object()

    def fake_get_generate_and_persist_service(
        *,
        generation_service,
        persistence_service,
    ):
        assert generation_service is not None
        assert persistence_service is not None

        return object()

    def fake_get_generate_planned_service(
        *,
        generation_service,
        physiological_test_service,
    ):
        assert generation_service is not None

        return object()

    monkeypatch.setattr(
        dependencies,
        "get_planning_context_service",
        fake_get_planning_context_service,
    )

    monkeypatch.setattr(
        dependencies,
        "get_weekly_planning_context_builder",
        fake_get_weekly_planning_context_builder,
    )

    monkeypatch.setattr(
        dependencies,
        "get_athlete_weekly_training_generation_service",
        fake_get_athlete_generation_service,
    )

    monkeypatch.setattr(
        dependencies,
        "get_generate_and_persist_training_week_service",
        fake_get_generate_and_persist_service,
    )

    monkeypatch.setattr(
        dependencies,
        "get_generate_planned_training_week_service",
        fake_get_generate_planned_service,
    )

    service = (
        dependencies
        .build_weekly_debrief_application_service(
            session
        )
    )

    planning_application = (
        service
        ._orchestrator
        ._planning_application_service
    )

    context_factory = (
        service._planning_context_factory
    )

    planning_factory = (
        planning_application
        ._planning_service_factory
    )

    assert callable(
        context_factory
    )
    assert callable(
        planning_factory
    )

    for athlete in athletes:
        context_factory(
            athlete.id
        )

    for athlete in athletes:
        planning_factory(
            athlete.id
        )

    assert context_user_ids == [
        user.id
        for user in users
    ]

    assert generation_user_ids == [
        user.id
        for user in users
    ]

    # Vérification supplémentaire du mapping SQL réel.
    for user, athlete in zip(
        users,
        athletes,
        strict=True,
    ):
        owner = session.scalar(
            select(
                AthleteProfile.user_id
            ).where(
                AthleteProfile.id
                == athlete.id
            )
        )

        assert owner == user.id


def test_default_context_factory_failure_isolated_a_b_c(
    session: Session,
    monkeypatch,
) -> None:
    """Une erreur de composition de B ne doit pas bloquer A et C."""

    from datetime import datetime, timezone

    import opencoach.api.coaching.dependencies as dependencies

    from opencoach.coaching.weekly_debrief_application import (
        WeeklyDebriefApplicationService,
    )
    from opencoach.coaching.weekly_debrief_eligibility import (
        WeeklyClosureEligibility,
    )
    from opencoach.coaching.weekly_debrief_orchestrator import (
        WeeklyDebriefOrchestrationBatch,
        WeeklyDebriefOrchestrationResult,
        WeeklyDebriefOrchestrationStatus,
    )
    from opencoach.coaching.weekly_debrief_runtime_context import (
        WeeklyDebriefRuntimeFacts,
    )

    users, athletes = _create_sql_profiles(
        session
    )

    user_a, user_b, user_c = users
    athlete_a, athlete_b, athlete_c = athletes

    resolved_users = []

    class FakePreparedContext:
        planning_input = object()
        sport_disciplines = ()

    class FakeContextBuilder:
        def build(
            self,
            *,
            athlete_profile_id,
            planning_date,
            trajectory_start_date,
        ):
            return FakePreparedContext()

    def fake_get_planning_context_service(
        *,
        user_id,
        db,
        readiness_service,
        training_stats_service,
    ):
        assert db is session

        resolved_users.append(
            user_id
        )

        if user_id == user_b.id:
            raise RuntimeError(
                "profile B context failure"
            )

        return object()

    def fake_get_weekly_planning_context_builder(
        *,
        planning_context_service,
        history_service,
    ):
        return FakeContextBuilder()

    monkeypatch.setattr(
        dependencies,
        "get_planning_context_service",
        fake_get_planning_context_service,
    )

    monkeypatch.setattr(
        dependencies,
        "get_weekly_planning_context_builder",
        fake_get_weekly_planning_context_builder,
    )

    composed = (
        dependencies
        .build_weekly_debrief_application_service(
            session
        )
    )

    default_context_factory = (
        composed._planning_context_factory
    )

    assert callable(
        default_context_factory
    )

    facts = WeeklyDebriefRuntimeFacts(
        week_start=WEEK_START,
        week_end=WEEK_END,
        has_remaining_planned_session=False,
        completed_sessions_count=1,
        last_completed_at=None,
        key_session_ids=frozenset(),
    )

    class IntegrationRuntime:
        def active_profile_ids(self):
            return (
                athlete_a.id,
                athlete_b.id,
                athlete_c.id,
            )

        def build_runtime_facts(
            self,
            *,
            athlete_profile_id,
            reference_date,
        ):
            assert athlete_profile_id in {
                athlete_a.id,
                athlete_b.id,
                athlete_c.id,
            }

            return facts

    class IntegrationOrchestrator:
        def __init__(self):
            self.contexts = ()

        def process_many(
            self,
            contexts,
        ):
            self.contexts = tuple(
                contexts
            )

            return WeeklyDebriefOrchestrationBatch(
                results=tuple(
                    WeeklyDebriefOrchestrationResult(
                        athlete_profile_id=(
                            context.athlete_profile_id
                        ),
                        status=(
                            WeeklyDebriefOrchestrationStatus.COMPLETED
                        ),
                        eligibility=(
                            WeeklyClosureEligibility.CLOSE
                        ),
                        reason=(
                            "integration completed"
                        ),
                    )
                    for context in self.contexts
                )
            )

    orchestrator = IntegrationOrchestrator()

    service = WeeklyDebriefApplicationService(
        runtime=IntegrationRuntime(),
        orchestrator=orchestrator,
        planning_context_factory=(
            default_context_factory
        ),
    )

    result = service.execute(
        reference_date=WEEK_END,
        now=datetime(
            2026,
            9,
            6,
            21,
            0,
            tzinfo=timezone.utc,
        ),
    )

    # Le mapping SQL doit être demandé dans l'ordre A/B/C.
    assert resolved_users == [
        user_a.id,
        user_b.id,
        user_c.id,
    ]

    # Seuls A et C atteignent l'orchestrateur.
    assert [
        context.athlete_profile_id
        for context in orchestrator.contexts
    ] == [
        athlete_a.id,
        athlete_c.id,
    ]

    # Le batch final conserve l'ordre original.
    assert [
        item.athlete_profile_id
        for item in result.results
    ] == [
        athlete_a.id,
        athlete_b.id,
        athlete_c.id,
    ]

    assert [
        item.status
        for item in result.results
    ] == [
        WeeklyDebriefOrchestrationStatus.COMPLETED,
        WeeklyDebriefOrchestrationStatus.FAILED,
        WeeklyDebriefOrchestrationStatus.COMPLETED,
    ]

    assert result.completed == 2
    assert result.failed == 1

    assert (
        "RuntimeError: profile B context failure"
        in (
            result.results[1].error
            or ""
        )
    )



def test_n_plus_one_persistence_is_strictly_scoped_by_profile(
    session: Session,
) -> None:
    """La même semaine N+1 reste isolée entre deux profils SQL."""

    from datetime import date

    from opencoach.coaching.generation import (
        WeeklyTrainingPersistenceService,
    )
    from opencoach.coaching.generation.models import (
        GeneratedTrainingWeek,
        GeneratedTrainingSession,
    )
    from opencoach.database.models import (
        TrainingSession as TrainingSessionModel,
        WeeklyTrainingPlan as WeeklyTrainingPlanModel,
    )
    from opencoach.database.repositories import (
        SqlTrainingSessionRepository,
        SqlWeeklyTrainingPlanRepository,
    )
    from opencoach.planning.weekly.training_envelope import (
        TrainingPhase,
    )

    users, athletes = _create_sql_profiles(
        session,
        count=2,
    )

    athlete_a, athlete_b = athletes

    week_start = date(
        2026,
        9,
        7,
    )
    week_end = date(
        2026,
        9,
        13,
    )

    from opencoach.planning.sessions.generators import (
        DeterministicSessionGenerator,
    )
    from opencoach.planning.sessions.coach_port import (
        SessionCoachRequest,
    )
    from opencoach.planning.sessions.intent import (
        SessionIntent,
        SessionIntentImportance,
    )
    from opencoach.planning.stimulus.training import (
        SpecificityLevel,
        SubstitutionPolicy,
        TrainingModality,
        TrainingStimulus,
    )
    from opencoach.planning.weekly.schedule_types import (
        FatigueBudget,
        Weekday,
    )
    from opencoach.planning.weekly.session_intent_slot import (
        WeeklySessionIntentSlot,
    )

    intent = SessionIntent(
        primary_stimulus=(
            TrainingStimulus.THRESHOLD
        ),
        secondary_stimuli=(),
        importance=(
            SessionIntentImportance.IMPORTANT
        ),
        specificity=SpecificityLevel.HIGH,
        substitution=(
            SubstitutionPolicy.ALLOWED
        ),
        preferred_modalities=(
            TrainingModality.RUNNING,
        ),
        required_modalities=(),
        duration_min_minutes=60,
        duration_max_minutes=60,
    )

    slot = WeeklySessionIntentSlot(
        slot_id="threshold",
        day=Weekday.WEDNESDAY,
        intent=intent,
        fatigue_budget=FatigueBudget.HIGH,
        duration_available_minutes=60,
    )

    proposal = (
        DeterministicSessionGenerator()
        .generate_session(
            request=SessionCoachRequest(
                phase=TrainingPhase.SPECIFIC,
                slot=slot,
            )
        )
    )

    generated_session = GeneratedTrainingSession(
        slot_id="threshold",
        date=date(
            2026,
            9,
            9,
        ),
        day=Weekday.WEDNESDAY,
        phase=TrainingPhase.SPECIFIC,
        proposal=proposal,
    )

    generated_week = GeneratedTrainingWeek(
        week_start=week_start,
        week_end=week_end,
        phase=TrainingPhase.SPECIFIC,
        sessions=(
            generated_session,
        ),
        target_load=300.0,
    )

    class Envelope:
        def __init__(self):
            self.week_start = week_start
            self.week_end = week_end
            self.phase = TrainingPhase.SPECIFIC
            self.week_type = "loading"
            self.phase_week_index = 1
            self.target_load = 300.0
            self.load_min = 285.0
            self.load_max = 315.0
            self.reference_duration_minutes = 240.0
            self.target_duration_minutes = 240.0
            self.long_endurance_reference_minutes = 90.0
            self.schedule_pressure = "normal"
            self.athlete_schedule_constrained = False

    repository = SqlTrainingSessionRepository(
        session
    )

    plan_repository = (
        SqlWeeklyTrainingPlanRepository(
            session
        )
    )

    persistence = WeeklyTrainingPersistenceService(
        repository=repository,
        weekly_plan_repository=(
            plan_repository
        ),
    )

    persisted_a = persistence.persist(
        athlete_profile_id=athlete_a.id,
        week=generated_week,
        envelope=Envelope(),
    )

    persisted_b = persistence.persist(
        athlete_profile_id=athlete_b.id,
        week=generated_week,
        envelope=Envelope(),
    )

    assert len(persisted_a) == 1
    assert len(persisted_b) == 1

    assert (
        persisted_a[0].id
        != persisted_b[0].id
    )

    # ---------------------------------------------------------
    # Vérification SQL brute des training_sessions
    # ---------------------------------------------------------

    sql_sessions_a = (
        session.execute(
            select(
                TrainingSessionModel
            ).where(
                TrainingSessionModel.athlete_profile_id
                == athlete_a.id
            )
        )
        .scalars()
        .all()
    )

    sql_sessions_b = (
        session.execute(
            select(
                TrainingSessionModel
            ).where(
                TrainingSessionModel.athlete_profile_id
                == athlete_b.id
            )
        )
        .scalars()
        .all()
    )

    assert len(sql_sessions_a) == 1
    assert len(sql_sessions_b) == 1

    assert (
        sql_sessions_a[0].athlete_profile_id
        == athlete_a.id
    )
    assert (
        sql_sessions_b[0].athlete_profile_id
        == athlete_b.id
    )

    assert (
        sql_sessions_a[0].id
        != sql_sessions_b[0].id
    )

    assert (
        sql_sessions_a[0].date
        == sql_sessions_b[0].date
    )

    # ---------------------------------------------------------
    # Vérification SQL brute des weekly_training_plans
    # ---------------------------------------------------------

    sql_plans_a = (
        session.execute(
            select(
                WeeklyTrainingPlanModel
            ).where(
                WeeklyTrainingPlanModel.athlete_profile_id
                == athlete_a.id
            )
        )
        .scalars()
        .all()
    )

    sql_plans_b = (
        session.execute(
            select(
                WeeklyTrainingPlanModel
            ).where(
                WeeklyTrainingPlanModel.athlete_profile_id
                == athlete_b.id
            )
        )
        .scalars()
        .all()
    )

    assert len(sql_plans_a) == 1
    assert len(sql_plans_b) == 1

    assert (
        sql_plans_a[0].athlete_profile_id
        == athlete_a.id
    )
    assert (
        sql_plans_b[0].athlete_profile_id
        == athlete_b.id
    )

    assert (
        sql_plans_a[0].week_start
        == week_start
    )
    assert (
        sql_plans_b[0].week_start
        == week_start
    )

    assert (
        sql_plans_a[0].id
        != sql_plans_b[0].id
    )

    # ---------------------------------------------------------
    # Vérification repository scoped
    # ---------------------------------------------------------

    plan_a = (
        plan_repository.get_plan_for_week(
            athlete_a.id,
            week_start,
        )
    )

    plan_b = (
        plan_repository.get_plan_for_week(
            athlete_b.id,
            week_start,
        )
    )

    assert plan_a is not None
    assert plan_b is not None

    assert (
        plan_a.athlete_profile_id
        == athlete_a.id
    )
    assert (
        plan_b.athlete_profile_id
        == athlete_b.id
    )

    assert plan_a.id != plan_b.id

    # Deux profils, même date et même planning_key :
    # aucune collision ni réconciliation croisée.
    assert (
        sql_sessions_a[0].planning_key
        == sql_sessions_b[0].planning_key
    )


def test_no_debrief_multi_profile_a_b_c_is_strictly_isolated(
    session: Session,
) -> None:
    """
    Vérifie le routage multi-profils lorsque B n'a réalisé
    aucune séance pendant la semaine fermée.

    A : 1 completed -> pipeline normal
    B : 0 completed -> NO_DEBRIEF
    C : 1 completed -> pipeline normal
    """
    from datetime import datetime, timezone
    from types import SimpleNamespace

    from opencoach.coaching.weekly_debrief_application import (
        WeeklyDebriefApplicationService,
        WeeklyDebriefPlanningContext,
    )
    from opencoach.coaching.weekly_debrief_orchestrator import (
        WeeklyDebriefOrchestrationStatus,
        WeeklyDebriefOrchestrator,
    )
    from opencoach.coaching.weekly_debrief_runtime_context import (
        WeeklyDebriefRuntimeFacts,
    )

    _, athletes = _create_sql_profiles(
        session,
        count=3,
    )

    athlete_a, athlete_b, athlete_c = athletes

    completed_by_profile = {
        athlete_a.id: 1,
        athlete_b.id: 0,
        athlete_c.id: 1,
    }

    class IntegrationRuntime:
        def active_profile_ids(self):
            return (
                athlete_a.id,
                athlete_b.id,
                athlete_c.id,
            )

        def build_runtime_facts(
            self,
            *,
            athlete_profile_id,
            reference_date,
        ):
            assert reference_date == WEEK_END

            return WeeklyDebriefRuntimeFacts(
                week_start=WEEK_START,
                week_end=WEEK_END,
                has_remaining_planned_session=False,
                completed_sessions_count=(
                    completed_by_profile[
                        athlete_profile_id
                    ]
                ),
                last_completed_at=None,
                key_session_ids=frozenset(),
            )

    planning_context_calls = []

    def planning_context_factory(
        athlete_profile_id,
    ):
        planning_context_calls.append(
            athlete_profile_id
        )

        class Resolver:
            def resolve(
                self,
                *,
                athlete_profile_id,
                reference_date,
                runtime_facts,
            ):
                assert reference_date == WEEK_END

                assert (
                    runtime_facts.completed_sessions_count
                    == 1
                )

                return WeeklyDebriefPlanningContext(
                    planning_input=object(),
                )

        return Resolver()

    closure_calls = []

    class ClosureService:
        def execute(
            self,
            **kwargs,
        ):
            athlete_profile_id = kwargs[
                "athlete_profile_id"
            ]

            closure_calls.append(
                athlete_profile_id
            )

            return object()

    planning_calls = []

    class PlanningApplicationService:
        def execute(
            self,
            **kwargs,
        ):
            athlete_profile_id = kwargs[
                "athlete_profile_id"
            ]

            planning_calls.append(
                athlete_profile_id
            )

            assert (
                kwargs["closed_week_start"]
                == WEEK_START
            )

            assert (
                kwargs["planning_input"]
                is not None
            )

            return SimpleNamespace(
                already_applied=False,
            )

    orchestrator = WeeklyDebriefOrchestrator(
        closure_service=ClosureService(),
        planning_application_service=(
            PlanningApplicationService()
        ),
    )

    application = WeeklyDebriefApplicationService(
        runtime=IntegrationRuntime(),
        orchestrator=orchestrator,
        planning_context_factory=(
            planning_context_factory
        ),
    )

    batch = application.execute(
        reference_date=WEEK_END,
        now=datetime(
            2026,
            9,
            6,
            21,
            0,
            tzinfo=timezone.utc,
        ),
    )

    assert [
        result.athlete_profile_id
        for result in batch.results
    ] == [
        athlete_a.id,
        athlete_b.id,
        athlete_c.id,
    ]

    assert [
        result.status
        for result in batch.results
    ] == [
        WeeklyDebriefOrchestrationStatus.COMPLETED,
        WeeklyDebriefOrchestrationStatus.NO_DEBRIEF,
        WeeklyDebriefOrchestrationStatus.COMPLETED,
    ]

    # Le contexte N+1 n'est résolu que pour A et C.
    assert planning_context_calls == [
        athlete_a.id,
        athlete_c.id,
    ]

    # La fermeture du débrief ne concerne que A et C.
    assert closure_calls == [
        athlete_a.id,
        athlete_c.id,
    ]

    # Le planning/adaptation N+1 ne concerne que A et C.
    assert planning_calls == [
        athlete_a.id,
        athlete_c.id,
    ]

    # B reste un résultat bénin et n'est jamais un échec.
    assert batch.completed == 2
    assert batch.no_debrief == 1
    assert batch.already_completed == 0
    assert batch.waiting == 0
    assert batch.failed == 0

