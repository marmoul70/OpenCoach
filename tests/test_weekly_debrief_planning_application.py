from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import date, datetime, timezone
from uuid import UUID, uuid4

import pytest

from opencoach.coaching.weekly_adaptation import (
    WeeklyAdaptationDecision,
    build_weekly_adaptation_decision,
)
from opencoach.coaching.weekly_debrief import (
    WeeklyDebriefFacts,
    build_weekly_debrief,
)
from opencoach.coaching.weekly_debrief_closure import (
    serialize_weekly_adaptation_decision,
)
from opencoach.coaching.weekly_debrief_planning_application import (
    WeeklyAdaptationPayloadError,
    WeeklyDebriefNotClosedError,
    WeeklyDebriefPlanningApplicationService,
    WeeklyPlanningApplicationError,
    deserialize_weekly_adaptation_decision,
)


WEEK_START = date(2026, 8, 31)
NEXT_WEEK_START = date(2026, 9, 7)


@dataclass(frozen=True)
class FakeStoredDebrief:
    adaptation_payload: dict | None
    planning_updated_at: datetime | None = None


class FakeRepository:
    def __init__(
        self,
        *,
        stored=None,
        marked=None,
    ):
        self.stored = stored
        self.marked = marked
        self.get_calls = []
        self.mark_calls = []

    def get_for_week(
        self,
        athlete_profile_id,
        week_start,
    ):
        self.get_calls.append(
            (
                athlete_profile_id,
                week_start,
            )
        )
        return self.stored

    def mark_planning_updated(
        self,
        athlete_profile_id,
        week_start,
        *,
        timestamp=None,
    ):
        self.mark_calls.append(
            (
                athlete_profile_id,
                week_start,
                timestamp,
            )
        )

        if self.marked is not None:
            return self.marked

        if self.stored is None:
            return None

        return FakeStoredDebrief(
            adaptation_payload=(
                self.stored.adaptation_payload
            ),
            planning_updated_at=datetime.now(
                timezone.utc
            ),
        )


class FakePlanningService:
    def __init__(
        self,
        result=None,
    ):
        self.result = (
            result
            if result is not None
            else object()
        )
        self.calls = []

    def execute(self, **kwargs):
        self.calls.append(kwargs)
        return self.result


def _decision() -> WeeklyAdaptationDecision:
    facts = WeeklyDebriefFacts(
        week_start=WEEK_START,
        week_end=date(2026, 9, 6),
        planned_sessions=4,
        completed_sessions=4,
        skipped_sessions=0,
        supplementary_sessions=0,
        planned_duration_minutes=240,
        actual_duration_minutes=240,
        planned_load=300.0,
        actual_load=300.0,
        key_sessions_planned=1,
        key_sessions_completed=1,
        compliant_intensity_sessions=1,
        analyzed_intensity_sessions=1,
        history_confidence=1.0,
    )

    debrief = build_weekly_debrief(
        facts
    )

    return build_weekly_adaptation_decision(
        debrief
    )


def _payload() -> dict:
    payload = (
        serialize_weekly_adaptation_decision(
            _decision()
        )
    )

    # Vérifie également que T6.5.3 produit bien du JSON.
    json.dumps(payload)

    return payload


def test_deserializes_persisted_decision() -> None:
    expected = _decision()

    actual = (
        deserialize_weekly_adaptation_decision(
            _payload()
        )
    )

    assert actual == expected
    assert isinstance(
        actual,
        WeeklyAdaptationDecision,
    )


def test_missing_closed_debrief_is_rejected() -> None:
    repository = FakeRepository()
    planner = FakePlanningService()

    service = (
        WeeklyDebriefPlanningApplicationService(
            debrief_repository=repository,
            planning_service=planner,
        )
    )

    with pytest.raises(
        WeeklyDebriefNotClosedError
    ):
        service.execute(
            athlete_profile_id=uuid4(),
            closed_week_start=WEEK_START,
            planning_input=object(),
        )

    assert planner.calls == []
    assert repository.mark_calls == []


def test_already_applied_is_idempotent() -> None:
    stored = FakeStoredDebrief(
        adaptation_payload=_payload(),
        planning_updated_at=datetime.now(
            timezone.utc
        ),
    )

    repository = FakeRepository(
        stored=stored
    )
    planner = FakePlanningService()

    service = (
        WeeklyDebriefPlanningApplicationService(
            debrief_repository=repository,
            planning_service=planner,
        )
    )

    result = service.execute(
        athlete_profile_id=uuid4(),
        closed_week_start=WEEK_START,
        planning_input=object(),
    )

    assert result.already_applied is True
    assert result.stored_debrief is stored
    assert result.planning_result is None

    assert planner.calls == []
    assert repository.mark_calls == []


def test_applies_persisted_adaptation_then_marks() -> None:
    profile_id = uuid4()
    planning_input = object()
    planning_result = object()

    stored = FakeStoredDebrief(
        adaptation_payload=_payload(),
    )

    repository = FakeRepository(
        stored=stored
    )

    planner = FakePlanningService(
        result=planning_result
    )

    service = (
        WeeklyDebriefPlanningApplicationService(
            debrief_repository=repository,
            planning_service=planner,
        )
    )

    result = service.execute(
        athlete_profile_id=profile_id,
        closed_week_start=WEEK_START,
        planning_input=planning_input,
    )

    assert result.already_applied is False
    assert result.planning_result is planning_result
    assert result.stored_debrief.planning_updated_at is not None

    assert len(planner.calls) == 1

    call = planner.calls[0]

    assert call["athlete_profile_id"] == profile_id
    assert call["planning_input"] is planning_input

    assert isinstance(
        call["weekly_adaptation"],
        WeeklyAdaptationDecision,
    )

    assert call["weekly_adaptation"] == _decision()

    assert len(repository.mark_calls) == 1
    assert repository.mark_calls[0][0] == profile_id
    assert repository.mark_calls[0][1] == WEEK_START


def test_forwards_generation_context() -> None:
    stored = FakeStoredDebrief(
        adaptation_payload=_payload()
    )

    repository = FakeRepository(
        stored=stored
    )
    planner = FakePlanningService()

    service = (
        WeeklyDebriefPlanningApplicationService(
            debrief_repository=repository,
            planning_service=planner,
        )
    )

    reference_date = date(
        2026,
        9,
        7,
    )

    reconcile_date = date(
        2026,
        9,
        7,
    )

    disciplines = (
        "running",
        "strength",
    )

    context = (
        "Débrief hebdomadaire fermé.",
    )

    service.execute(
        athlete_profile_id=uuid4(),
        closed_week_start=WEEK_START,
        planning_input=object(),
        physiological_reference_date=(
            reference_date
        ),
        sport_disciplines=disciplines,
        reconcile_from_date=(
            reconcile_date
        ),
        additional_context=context,
    )

    call = planner.calls[0]

    assert (
        call["physiological_reference_date"]
        == reference_date
    )
    assert (
        call["sport_disciplines"]
        == disciplines
    )
    assert (
        call["reconcile_from_date"]
        == reconcile_date
    )
    assert (
        call["additional_context"]
        == context
    )


def test_missing_adaptation_payload_is_rejected() -> None:
    repository = FakeRepository(
        stored=FakeStoredDebrief(
            adaptation_payload=None
        )
    )

    planner = FakePlanningService()

    service = (
        WeeklyDebriefPlanningApplicationService(
            debrief_repository=repository,
            planning_service=planner,
        )
    )

    with pytest.raises(
        WeeklyAdaptationPayloadError
    ):
        service.execute(
            athlete_profile_id=uuid4(),
            closed_week_start=WEEK_START,
            planning_input=object(),
        )

    assert planner.calls == []
    assert repository.mark_calls == []


def test_invalid_adaptation_payload_is_rejected() -> None:
    payload = _payload()
    payload.pop(
        "direction"
    )

    repository = FakeRepository(
        stored=FakeStoredDebrief(
            adaptation_payload=payload
        )
    )

    planner = FakePlanningService()

    service = (
        WeeklyDebriefPlanningApplicationService(
            debrief_repository=repository,
            planning_service=planner,
        )
    )

    with pytest.raises(
        WeeklyAdaptationPayloadError
    ):
        service.execute(
            athlete_profile_id=uuid4(),
            closed_week_start=WEEK_START,
            planning_input=object(),
        )

    assert planner.calls == []
    assert repository.mark_calls == []


def test_failed_marker_is_reported_after_planning() -> None:
    stored = FakeStoredDebrief(
        adaptation_payload=_payload()
    )

    class RepositoryWithoutMarker(
        FakeRepository
    ):
        def mark_planning_updated(
            self,
            athlete_profile_id,
            week_start,
            *,
            timestamp=None,
        ):
            self.mark_calls.append(
                (
                    athlete_profile_id,
                    week_start,
                    timestamp,
                )
            )
            return None

    repository = RepositoryWithoutMarker(
        stored=stored
    )

    planner = FakePlanningService()

    service = (
        WeeklyDebriefPlanningApplicationService(
            debrief_repository=repository,
            planning_service=planner,
        )
    )

    with pytest.raises(
        WeeklyPlanningApplicationError
    ):
        service.execute(
            athlete_profile_id=uuid4(),
            closed_week_start=WEEK_START,
            planning_input=object(),
        )

    # Le moteur a réussi : seule la persistance du marqueur échoue.
    assert len(planner.calls) == 1
    assert len(repository.mark_calls) == 1


def test_planning_application_uses_profile_scoped_service_factory() -> None:
    """A et B ne doivent jamais partager leur planning service."""
    athlete_a = uuid4()
    athlete_b = uuid4()

    stored = FakeStoredDebrief(
        adaptation_payload=_payload(),
    )

    repository = FakeRepository(
        stored=stored,
    )

    planner_a = FakePlanningService(
        result=object(),
    )
    planner_b = FakePlanningService(
        result=object(),
    )

    factory_calls = []

    def planning_service_factory(
        athlete_profile_id,
    ):
        factory_calls.append(
            athlete_profile_id
        )

        if athlete_profile_id == athlete_a:
            return planner_a

        if athlete_profile_id == athlete_b:
            return planner_b

        raise AssertionError(
            "Profil inattendu."
        )

    service = (
        WeeklyDebriefPlanningApplicationService(
            debrief_repository=repository,
            planning_service_factory=(
                planning_service_factory
            ),
        )
    )

    service.execute(
        athlete_profile_id=athlete_a,
        closed_week_start=WEEK_START,
        planning_input=object(),
    )

    service.execute(
        athlete_profile_id=athlete_b,
        closed_week_start=WEEK_START,
        planning_input=object(),
    )

    assert factory_calls == [
        athlete_a,
        athlete_b,
    ]

    assert len(planner_a.calls) == 1
    assert len(planner_b.calls) == 1

    assert (
        planner_a.calls[0][
            "athlete_profile_id"
        ]
        == athlete_a
    )

    assert (
        planner_b.calls[0][
            "athlete_profile_id"
        ]
        == athlete_b
    )


class RecordingWorkoutSyncService:
    def __init__(self, error=None):
        self.calls = []
        self.error = error

    def sync_period(
        self,
        *,
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

        if self.error is not None:
            raise self.error

        return object()


def test_syncs_next_week_after_successful_planning() -> None:
    athlete_profile_id = uuid4()
    closed_week_start = date(2026, 8, 31)

    stored = FakeStoredDebrief(
        adaptation_payload=_payload(),
    )

    repository = FakeRepository(
        stored=stored,
    )
    planning = FakePlanningService()
    sync = RecordingWorkoutSyncService()

    service = WeeklyDebriefPlanningApplicationService(
        debrief_repository=repository,
        planning_service=planning,
        workout_sync_service=sync,
    )

    result = service.execute(
        athlete_profile_id=athlete_profile_id,
        closed_week_start=closed_week_start,
        planning_input=object(),
    )

    assert result.already_applied is False

    assert sync.calls == [
        (
            athlete_profile_id,
            date(2026, 9, 7),
            date(2026, 9, 13),
        )
    ]


def test_sync_failure_does_not_invalidate_planning() -> None:
    athlete_profile_id = uuid4()
    closed_week_start = date(2026, 8, 31)

    stored = FakeStoredDebrief(
        adaptation_payload=_payload(),
    )

    repository = FakeRepository(
        stored=stored,
    )
    planning = FakePlanningService()

    sync = RecordingWorkoutSyncService(
        error=RuntimeError(
            "Intervals indisponible"
        )
    )

    service = WeeklyDebriefPlanningApplicationService(
        debrief_repository=repository,
        planning_service=planning,
        workout_sync_service=sync,
    )

    result = service.execute(
        athlete_profile_id=athlete_profile_id,
        closed_week_start=closed_week_start,
        planning_input=object(),
    )

    assert result.already_applied is False

    assert sync.calls == [
        (
            athlete_profile_id,
            date(2026, 9, 7),
            date(2026, 9, 13),
        )
    ]


def test_already_applied_planning_does_not_sync_again() -> None:
    athlete_profile_id = uuid4()
    closed_week_start = date(2026, 8, 31)

    stored = FakeStoredDebrief(
        adaptation_payload=_payload(),
        planning_updated_at=datetime(
            2026,
            9,
            6,
            18,
            0,
            tzinfo=timezone.utc,
        ),
    )

    repository = FakeRepository(
        stored=stored,
    )
    planning = FakePlanningService()
    sync = RecordingWorkoutSyncService()

    service = WeeklyDebriefPlanningApplicationService(
        debrief_repository=repository,
        planning_service=planning,
        workout_sync_service=sync,
    )

    result = service.execute(
        athlete_profile_id=athlete_profile_id,
        closed_week_start=closed_week_start,
        planning_input=object(),
    )

    assert result.already_applied is True
    assert sync.calls == []
