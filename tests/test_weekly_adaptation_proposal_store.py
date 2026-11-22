from datetime import date
from uuid import uuid4

from opencoach.coaching.weekly_adaptation_proposal_store import (
    WeeklyAdaptationProposalStore,
)


def test_proposal_is_stored_outside_database_and_readable(tmp_path) -> None:
    athlete_id = uuid4()
    week_start = date(2026, 11, 16)
    store = WeeklyAdaptationProposalStore(root=tmp_path)
    payload = {"direction": "reduce_load", "sessions": []}

    path = store.save(athlete_id, week_start, payload)

    assert path.is_file()
    assert path.suffix == ".json"
    assert store.get(athlete_id, week_start) == payload


def test_proposal_can_be_deleted_after_rejection_or_manual_session(tmp_path) -> None:
    athlete_id = uuid4()
    week_start = date(2026, 11, 16)
    store = WeeklyAdaptationProposalStore(root=tmp_path)
    store.save(athlete_id, week_start, {"direction": "maintain"})

    assert store.delete(athlete_id, week_start) is True
    assert store.get(athlete_id, week_start) is None
    assert store.delete(athlete_id, week_start) is False


def test_proposals_are_isolated_by_athlete_and_week(tmp_path) -> None:
    first_athlete = uuid4()
    second_athlete = uuid4()
    week_start = date(2026, 11, 16)
    store = WeeklyAdaptationProposalStore(root=tmp_path)

    store.save(first_athlete, week_start, {"value": 1})
    store.save(second_athlete, week_start, {"value": 2})

    assert store.get(first_athlete, week_start) == {"value": 1}
    assert store.get(second_athlete, week_start) == {"value": 2}
