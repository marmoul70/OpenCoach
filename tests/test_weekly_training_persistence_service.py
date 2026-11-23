from datetime import date
from uuid import uuid4

import pytest

from opencoach.coaching.generation.persistence import (
    ExistingTrainingSessionConflictError,
    WeeklyTrainingPersistenceService,
)
from opencoach.coaching.generation.models import (
    GeneratedTrainingWeek,
)
from opencoach.models import (
    TrainingSession,
)
from opencoach.planning.weekly.training_envelope import (
    TrainingPhase,
)

from test_generated_training_session_mapper import (
    create_generated_session,
)


class FakeTrainingSessionRepository:
    def __init__(
        self,
        sessions=(),
    ) -> None:
        self.sessions = list(
            sessions
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

        if session.id is None:
            session.id = uuid4()
            self.sessions.append(
                session
            )
            return session

        for index, existing in enumerate(
            self.sessions
        ):
            if existing.id == session.id:
                self.sessions[
                    index
                ] = session
                return session

        self.sessions.append(
            session
        )

        return session

    def delete_session(
        self,
        athlete_profile_id,
        session_id,
    ):
        del athlete_profile_id

        self.sessions = [
            session
            for session in self.sessions
            if session.id != session_id
        ]

def create_week():
    generated = (
        create_generated_session()
    )

    return GeneratedTrainingWeek(
        week_start=date(
            2027,
            7,
            5,
        ),
        week_end=date(
            2027,
            7,
            11,
        ),
        phase=TrainingPhase.SPECIFIC,
        sessions=(
            generated,
        ),
        target_load=420.0,
    )


def create_existing_session(
    *,
    status="planned",
):
    return TrainingSession(
        id=uuid4(),
        date=date(
            2027,
            7,
            7,
        ),
        type="easy",
        sport_type="Run",
        title="Ancienne séance",
        description="Ancienne séance.",
        duration_minutes=45,
        status=status,
        planning_key=(
            "2027-07-05:threshold"
        ),
    )



class FakeWeeklyTrainingPlanRepository:
    """Double de test du repository de plan hebdomadaire."""

    def __init__(self) -> None:
        self.saved_plans = []

    def save_plan(self, plan):
        self.saved_plans.append(plan)
        return plan

    def get_plan_for_week(
        self,
        athlete_profile_id,
        week_start,
    ):
        for plan in reversed(
            self.saved_plans
        ):
            if (
                plan.athlete_profile_id
                == athlete_profile_id
                and plan.week_start
                == week_start
            ):
                return plan

        return None


class FakeWeeklyEnvelope:
    """Enveloppe minimale nécessaire à la persistance."""

    def __init__(
        self,
        *,
        week_start,
        week_end,
        phase,
    ) -> None:
        self.week_start = week_start
        self.week_end = week_end
        self.phase = phase
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


def create_persistence_service(
    repository,
):
    return WeeklyTrainingPersistenceService(
        repository=repository,
        weekly_plan_repository=(
            FakeWeeklyTrainingPlanRepository()
        ),
    )


def create_envelope_for_week(
    week,
):
    return FakeWeeklyEnvelope(
        week_start=week.week_start,
        week_end=week.week_end,
        phase=week.phase,
    )


def test_persists_new_generated_session() -> None:
    repository = (
        FakeTrainingSessionRepository()
    )

    service = (
        create_persistence_service(repository)
    )

    persisted = service.persist(
        athlete_profile_id=uuid4(),
        week=create_week(),
        envelope=create_envelope_for_week(
            create_week()
        ),
    )

    assert len(
        persisted
    ) == 1

    assert persisted[0].id is not None

    assert (
        persisted[0].title
        == "Travail au seuil"
    )


def test_existing_planned_session_is_updated() -> None:
    existing = (
        create_existing_session()
    )

    repository = (
        FakeTrainingSessionRepository(
            (
                existing,
            )
        )
    )

    service = (
        create_persistence_service(repository)
    )

    persisted = service.persist(
        athlete_profile_id=uuid4(),
        week=create_week(),
        envelope=create_envelope_for_week(
            create_week()
        ),
    )

    assert (
        persisted[0].id
        == existing.id
    )

    assert (
        persisted[0].title
        == "Travail au seuil"
    )


def test_completed_session_is_never_overwritten() -> None:
    repository = (
        FakeTrainingSessionRepository(
            (
                create_existing_session(
                    status="completed"
                ),
            )
        )
    )

    service = (
        create_persistence_service(repository)
    )

    with pytest.raises(
        ExistingTrainingSessionConflictError
    ):
        service.persist(
            athlete_profile_id=uuid4(),
            week=create_week(),
            envelope=create_envelope_for_week(
                create_week()
            ),
        )

def test_two_sessions_on_same_day_are_independent() -> None:
    first = (
        create_generated_session()
    )

    second = (
        create_generated_session()
    )

    object.__setattr__(
        second,
        "slot_id",
        "strength",
    )

    week = GeneratedTrainingWeek(
        week_start=date(
            2027,
            7,
            5,
        ),
        week_end=date(
            2027,
            7,
            11,
        ),
        phase=TrainingPhase.SPECIFIC,
        sessions=(
            first,
            second,
        ),
    )

    repository = (
        FakeTrainingSessionRepository()
    )

    service = (
        create_persistence_service(repository)
    )

    persisted = service.persist(
        athlete_profile_id=uuid4(),
        week=week,

            envelope=create_envelope_for_week(
                week
            ),    )

    assert len(
        persisted
    ) == 2

    assert (
        persisted[0].planning_key
        != persisted[1].planning_key
    )

def test_obsolete_generated_planned_session_is_removed() -> None:
    """Une ancienne séance générée devenue obsolète est supprimée."""

    obsolete = TrainingSession(
        id=uuid4(),
        date=date(
            2027,
            7,
            9,
        ),
        type="aerobic_easy",
        sport_type="Run",
        title="Ancienne endurance",
        description="Ancienne séance générée.",
        duration_minutes=60,
        status="planned",
        planning_key=(
            "2027-07-05:obsolete-slot"
        ),
    )

    repository = (
        FakeTrainingSessionRepository(
            (
                obsolete,
            )
        )
    )

    service = (
        create_persistence_service(repository)
    )

    service.persist(
        athlete_profile_id=uuid4(),
        week=create_week(),
        envelope=create_envelope_for_week(
            create_week()
        ),
    )

    assert all(
        session.id != obsolete.id
        for session in repository.sessions
    )


def test_manual_planned_session_is_preserved() -> None:
    """Une séance planifiée non générée par OpenCoach est conservée."""

    manual = TrainingSession(
        id=uuid4(),
        date=date(
            2027,
            7,
            9,
        ),
        type="aerobic_easy",
        sport_type="Run",
        title="Séance manuelle",
        description="Séance ajoutée manuellement.",
        duration_minutes=45,
        status="planned",
        planning_key=None,
    )

    repository = (
        FakeTrainingSessionRepository(
            (
                manual,
            )
        )
    )

    service = (
        create_persistence_service(repository)
    )

    service.persist(
        athlete_profile_id=uuid4(),
        week=create_week(),
        envelope=create_envelope_for_week(
            create_week()
        ),
    )

    assert any(
        session.id == manual.id
        for session in repository.sessions
    )


def test_obsolete_session_with_coros_identity_is_preserved() -> None:
    """Une séance déjà planifiée sur COROS n'est jamais supprimée localement."""
    remote = create_existing_session()
    remote.coros_workout_id = "coros-id-obsolete"
    remote.coros_scheduled_date = remote.date
    remote.coros_sync_status = "synced"
    repository = FakeTrainingSessionRepository((remote,))
    service = create_persistence_service(repository)

    service.persist(
        athlete_profile_id=uuid4(),
        week=create_week(),
        envelope=create_envelope_for_week(create_week()),
    )

    assert any(session.id == remote.id for session in repository.sessions)
    assert remote.coros_workout_id == "coros-id-obsolete"


def test_obsolete_session_with_coros_pending_state_is_preserved() -> None:
    remote = create_existing_session()
    remote.coros_sync_status = "pending"
    repository = FakeTrainingSessionRepository((remote,))
    service = create_persistence_service(repository)

    service.persist(
        athlete_profile_id=uuid4(),
        week=create_week(),
        envelope=create_envelope_for_week(create_week()),
    )

    assert any(session.id == remote.id for session in repository.sessions)


def test_obsolete_completed_session_is_preserved() -> None:
    """Une ancienne séance réalisée n'est jamais supprimée."""

    completed = TrainingSession(
        id=uuid4(),
        date=date(
            2027,
            7,
            9,
        ),
        type="aerobic_easy",
        sport_type="Run",
        title="Séance réalisée",
        description="Ancienne séance générée.",
        duration_minutes=60,
        status="completed",
        planning_key=(
            "2027-07-05:obsolete-slot"
        ),
    )

    repository = (
        FakeTrainingSessionRepository(
            (
                completed,
            )
        )
    )

    service = (
        create_persistence_service(repository)
    )

    service.persist(
        athlete_profile_id=uuid4(),
        week=create_week(),
        envelope=create_envelope_for_week(
            create_week()
        ),
    )

    assert any(
        session.id == completed.id
        for session in repository.sessions
    )

def test_obsolete_session_with_activity_is_preserved() -> None:
    """Une séance liée à une activité n'est jamais supprimée."""

    linked = TrainingSession(
        id=uuid4(),
        date=date(
            2027,
            7,
            9,
        ),
        type="aerobic_easy",
        sport_type="Run",
        title="Séance liée",
        description="Séance générée.",
        duration_minutes=60,
        status="planned",
        planning_key=(
            "2027-07-05:obsolete-slot"
        ),
        activity_id=uuid4(),
    )

    repository = (
        FakeTrainingSessionRepository(
            (
                linked,
            )
        )
    )

    service = (
        create_persistence_service(repository)
    )

    service.persist(
        athlete_profile_id=uuid4(),
        week=create_week(),
        envelope=create_envelope_for_week(
            create_week()
        ),
    )

    assert any(
        session.id == linked.id
        for session in repository.sessions
    )


def test_past_obsolete_generated_session_is_preserved_on_refresh() -> None:
    """Une séance passée ne peut pas être supprimée par un refresh."""

    past = TrainingSession(
        id=uuid4(),
        date=date(
            2027,
            7,
            5,
        ),
        type="aerobic_easy",
        sport_type="Run",
        title="Séance passée",
        description="Séance générée avant le refresh.",
        duration_minutes=45,
        status="planned",
        planning_key=(
            "2027-07-05:obsolete-past-slot"
        ),
    )

    repository = (
        FakeTrainingSessionRepository(
            (
                past,
            )
        )
    )

    service = (
        create_persistence_service(repository)
    )

    service.persist(
        athlete_profile_id=uuid4(),
        week=create_week(),
        envelope=create_envelope_for_week(
            create_week()
        ),
        reconcile_from_date=date(
            2027,
            7,
            6,
        ),
    )

    assert any(
        session.id == past.id
        for session in repository.sessions
    )


def test_past_generated_session_is_not_overwritten_on_refresh() -> None:
    """Une séance passée avec la même planning_key reste immuable."""

    past = create_existing_session()

    past.date = date(
        2027,
        7,
        5,
    )

    repository = (
        FakeTrainingSessionRepository(
            (
                past,
            )
        )
    )

    service = (
        create_persistence_service(repository)
    )

    original_title = past.title
    original_duration = (
        past.duration_minutes
    )

    persisted = service.persist(
        athlete_profile_id=uuid4(),
        week=create_week(),
        envelope=create_envelope_for_week(
            create_week()
        ),
        reconcile_from_date=date(
            2027,
            7,
            6,
        ),
    )

    assert persisted == ()

    stored = next(
        session
        for session in repository.sessions
        if session.id == past.id
    )

    assert (
        stored.title
        == original_title
    )

    assert (
        stored.duration_minutes
        == original_duration
    )


class FakeTransaction:
    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


class TransactionalTrainingSessionRepository(FakeTrainingSessionRepository):
    def __init__(self, transaction, *, fail_on_save=False) -> None:
        super().__init__()
        self.session = transaction
        self.fail_on_save = fail_on_save

    def save_session(self, athlete_profile_id, session, *, commit=True):
        if self.fail_on_save:
            raise RuntimeError("Échec simulé pendant l'enregistrement")
        return super().save_session(athlete_profile_id, session)


class TransactionalWeeklyPlanRepository(FakeWeeklyTrainingPlanRepository):
    def __init__(self, transaction) -> None:
        super().__init__()
        self.session = transaction

    def save_plan(self, plan, *, commit=True):
        self.saved_plans.append(plan)
        return plan


def test_sql_style_persistence_rolls_back_all_writes_on_failure() -> None:
    transaction = FakeTransaction()
    repository = TransactionalTrainingSessionRepository(
        transaction,
        fail_on_save=True,
    )
    plan_repository = TransactionalWeeklyPlanRepository(transaction)
    service = WeeklyTrainingPersistenceService(
        repository=repository,
        weekly_plan_repository=plan_repository,
    )
    week = create_week()

    with pytest.raises(RuntimeError, match="Échec simulé"):
        service.persist(
            athlete_profile_id=uuid4(),
            week=week,
            envelope=create_envelope_for_week(week),
        )

    assert len(plan_repository.saved_plans) == 1
    assert transaction.commits == 0
    assert transaction.rollbacks == 1


def test_conflict_does_not_persist_weekly_plan_or_change_sessions() -> None:
    """Un conflit doit être détecté avant toute écriture de planning."""
    completed = create_existing_session(status="completed")
    repository = FakeTrainingSessionRepository((completed,))
    plan_repository = FakeWeeklyTrainingPlanRepository()
    service = WeeklyTrainingPersistenceService(
        repository=repository,
        weekly_plan_repository=plan_repository,
    )
    week = create_week()
    original_title = completed.title

    with pytest.raises(ExistingTrainingSessionConflictError):
        service.persist(
            athlete_profile_id=uuid4(),
            week=week,
            envelope=create_envelope_for_week(week),
        )

    assert plan_repository.saved_plans == []
    assert len(repository.sessions) == 1
    assert repository.sessions[0].id == completed.id
    assert repository.sessions[0].title == original_title

