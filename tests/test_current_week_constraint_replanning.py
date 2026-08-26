from datetime import date
from uuid import uuid4

from opencoach.coaching.generation.identity import (
    build_planning_key,
)
from opencoach.coaching.generation.models import (
    GeneratedTrainingWeek,
)
from opencoach.coaching.generation.persistence import (
    WeeklyTrainingPersistenceService,
)
from opencoach.models import (
    AthleteConstraint,
    AthleteProfile,
    TrainingSession,
)
from opencoach.planning import (
    build_weekly_availability,
    rank_training_day_candidates,
)
from opencoach.planning.weekly.training_envelope import (
    TrainingPhase,
)

from test_generated_training_session_mapper import (
    create_generated_session,
)
from test_weekly_training_persistence_service import (
    FakeTrainingSessionRepository,
)


WEEK_START = date(
    2026,
    8,
    24,
)

MONDAY = date(
    2026,
    8,
    24,
)

TUESDAY = date(
    2026,
    8,
    25,
)

WEDNESDAY = date(
    2026,
    8,
    26,
)

THURSDAY = date(
    2026,
    8,
    27,
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


def _work_absence_on_wednesday() -> AthleteConstraint:
    return AthleteConstraint(
        id=uuid4(),
        start_date=WEDNESDAY,
        end_date=WEDNESDAY,
        constraint_type="work",
        availability="unavailable",
        running_allowed=False,
        cross_training_allowed=False,
        notes="Absence professionnelle",
    )


def _past_monday_session() -> TrainingSession:
    return TrainingSession(
        id=uuid4(),
        date=MONDAY,
        type="aerobic_easy",
        sport_type="Run",
        title="Endurance fondamentale",
        description="Séance déjà planifiée lundi.",
        duration_minutes=45,
        intensity="easy",
        status="planned",
        planning_key=(
            build_planning_key(
                week_start=WEEK_START,
                slot_id="monday-easy",
            )
        ),
    )


def _wednesday_threshold_session() -> TrainingSession:
    return TrainingSession(
        id=uuid4(),
        date=WEDNESDAY,
        type="threshold",
        sport_type="Run",
        title="Travail au seuil",
        description="Séance initialement prévue mercredi.",
        duration_minutes=60,
        intensity="hard",
        status="planned",
        planning_key=(
            build_planning_key(
                week_start=WEEK_START,
                slot_id="threshold",
            )
        ),
    )


def test_work_absence_moves_future_session_and_preserves_past(
) -> None:
    """Une absence mercredi replannifie le futur sans toucher au lundi."""

    athlete = _athlete()

    constraint = (
        _work_absence_on_wednesday()
    )

    availability = (
        build_weekly_availability(
            athlete=athlete,
            week_start=WEEK_START,
            constraints=(
                constraint,
            ),
        )
    )

    candidates = (
        rank_training_day_candidates(
            week=availability,
            original_date=WEDNESDAY,
            for_running=True,
        )
    )

    assert candidates

    # Règle métier déjà validée :
    # jeudi est préféré à mardi lorsqu'ils sont
    # autrement équivalents.
    selected = candidates[0]

    assert (
        selected.date
        == THURSDAY
    )

    assert (
        selected.date
        != WEDNESDAY
    )

    monday = (
        _past_monday_session()
    )

    threshold = (
        _wednesday_threshold_session()
    )

    original_monday_id = (
        monday.id
    )

    original_monday_title = (
        monday.title
    )

    original_threshold_id = (
        threshold.id
    )

    repository = (
        FakeTrainingSessionRepository(
            (
                monday,
                threshold,
            )
        )
    )

    generated = (
        create_generated_session()
    )

    # L'identité logique de la séance reste stable :
    # seul son placement change.
    object.__setattr__(
        generated,
        "slot_id",
        "threshold",
    )

    object.__setattr__(
        generated,
        "date",
        selected.date,
    )

    week = GeneratedTrainingWeek(
        week_start=WEEK_START,
        week_end=date(
            2026,
            8,
            30,
        ),
        phase=TrainingPhase.BUILD,
        sessions=(
            generated,
        ),
        target_load=300.0,
    )

    persistence = (
        WeeklyTrainingPersistenceService(
            repository=repository
        )
    )

    persisted = persistence.persist(
        athlete_profile_id=uuid4(),
        week=week,
        reconcile_from_date=TUESDAY,
    )

    assert len(
        persisted
    ) == 1

    moved = persisted[0]

    # La séance future garde son identité DB :
    # elle est réellement replanifiée,
    # pas dupliquée.
    assert (
        moved.id
        == original_threshold_id
    )

    assert (
        moved.date
        == THURSDAY
    )

    assert (
        moved.date
        != WEDNESDAY
    )

    # Le mercredi indisponible ne contient
    # plus la séance.
    assert not any(
        session.date == WEDNESDAY
        and session.id
        == original_threshold_id
        for session in repository.sessions
    )

    # Le lundi est antérieur à reconcile_from_date :
    # il reste totalement immuable.
    stored_monday = next(
        session
        for session in repository.sessions
        if session.id
        == original_monday_id
    )

    assert (
        stored_monday.date
        == MONDAY
    )

    assert (
        stored_monday.title
        == original_monday_title
    )

    # Pas de duplication de la séance déplacée.
    assert (
        sum(
            1
            for session
            in repository.sessions
            if session.id
            == original_threshold_id
        )
        == 1
    )
