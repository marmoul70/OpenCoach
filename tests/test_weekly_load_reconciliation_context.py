import pytest

from opencoach.planning.weekly_load_reconciliation import (
    LoadReconciliationStatus,
    WeeklyLoadReconciliation,
    reconcile_weekly_load,
)
from opencoach.planning.weekly_load_reconciliation_context import (
    ContextualWeeklyLoadReconciliation,
    LoadDeviationCause,
    contextualize_weekly_load_reconciliation,
)


def create_under_target_reconciliation() -> (
    WeeklyLoadReconciliation
):
    return reconcile_weekly_load(
        planned_load=550.0,
        actual_load=430.0,
    )


def test_under_target_can_be_explained_by_professional_constraint() -> None:
    reconciliation = create_under_target_reconciliation()

    result = contextualize_weekly_load_reconciliation(
        reconciliation=reconciliation,
        cause=LoadDeviationCause.PROFESSIONAL_CONSTRAINT,
        athlete_imposed=True,
    )

    assert (
        reconciliation.status
        is LoadReconciliationStatus.UNDER_TARGET
    )

    assert (
        result.cause
        is LoadDeviationCause.PROFESSIONAL_CONSTRAINT
    )

    assert result.athlete_imposed is True


def test_under_target_can_be_explained_by_fatigue() -> None:
    result = contextualize_weekly_load_reconciliation(
        reconciliation=create_under_target_reconciliation(),
        cause=LoadDeviationCause.FATIGUE,
    )

    assert result.cause is LoadDeviationCause.FATIGUE

    assert result.athlete_imposed is False


def test_under_target_can_be_explained_by_illness() -> None:
    result = contextualize_weekly_load_reconciliation(
        reconciliation=create_under_target_reconciliation(),
        cause=LoadDeviationCause.ILLNESS,
    )

    assert result.cause is LoadDeviationCause.ILLNESS


def test_under_target_can_be_explained_by_injury() -> None:
    result = contextualize_weekly_load_reconciliation(
        reconciliation=create_under_target_reconciliation(),
        cause=LoadDeviationCause.INJURY,
    )

    assert result.cause is LoadDeviationCause.INJURY


def test_over_target_can_be_explained_by_sport_event() -> None:
    reconciliation = reconcile_weekly_load(
        planned_load=400.0,
        actual_load=500.0,
    )

    result = contextualize_weekly_load_reconciliation(
        reconciliation=reconciliation,
        cause=LoadDeviationCause.SPORT_EVENT,
    )

    assert (
        reconciliation.status
        is LoadReconciliationStatus.OVER_TARGET
    )

    assert result.cause is LoadDeviationCause.SPORT_EVENT


def test_athlete_choice_can_be_explicit() -> None:
    result = contextualize_weekly_load_reconciliation(
        reconciliation=create_under_target_reconciliation(),
        cause=LoadDeviationCause.ATHLETE_CHOICE,
        athlete_imposed=True,
    )

    assert (
        result.cause
        is LoadDeviationCause.ATHLETE_CHOICE
    )

    assert result.athlete_imposed is True


def test_incomplete_data_can_explain_deviation() -> None:
    result = contextualize_weekly_load_reconciliation(
        reconciliation=create_under_target_reconciliation(),
        cause=LoadDeviationCause.INCOMPLETE_DATA,
    )

    assert (
        result.cause
        is LoadDeviationCause.INCOMPLETE_DATA
    )


def test_missing_cause_becomes_unknown_for_significant_deviation() -> None:
    result = contextualize_weekly_load_reconciliation(
        reconciliation=create_under_target_reconciliation(),
    )

    assert result.cause is LoadDeviationCause.UNKNOWN


def test_on_target_week_automatically_has_no_deviation_cause() -> None:
    reconciliation = reconcile_weekly_load(
        planned_load=500.0,
        actual_load=490.0,
    )

    result = contextualize_weekly_load_reconciliation(
        reconciliation=reconciliation,
    )

    assert (
        reconciliation.status
        is LoadReconciliationStatus.ON_TARGET
    )

    assert result.cause is LoadDeviationCause.NONE


def test_on_target_ignores_supplied_deviation_cause() -> None:
    reconciliation = reconcile_weekly_load(
        planned_load=500.0,
        actual_load=500.0,
    )

    result = contextualize_weekly_load_reconciliation(
        reconciliation=reconciliation,
        cause=LoadDeviationCause.FATIGUE,
    )

    assert result.cause is LoadDeviationCause.NONE


def test_context_can_preserve_note() -> None:
    result = contextualize_weekly_load_reconciliation(
        reconciliation=create_under_target_reconciliation(),
        cause=LoadDeviationCause.PROFESSIONAL_CONSTRAINT,
        note="Deux gardes cette semaine.",
    )

    assert result.note == "Deux gardes cette semaine."


def test_model_rejects_none_cause_for_significant_deviation() -> None:
    with pytest.raises(
        ValueError,
        match="cause",
    ):
        ContextualWeeklyLoadReconciliation(
            reconciliation=create_under_target_reconciliation(),
            cause=LoadDeviationCause.NONE,
        )


def test_model_rejects_deviation_cause_when_week_is_on_target() -> None:
    reconciliation = reconcile_weekly_load(
        planned_load=500.0,
        actual_load=500.0,
    )

    with pytest.raises(
        ValueError,
        match="conforme",
    ):
        ContextualWeeklyLoadReconciliation(
            reconciliation=reconciliation,
            cause=LoadDeviationCause.FATIGUE,
        )


@pytest.mark.parametrize(
    "cause",
    [
        LoadDeviationCause.PROFESSIONAL_CONSTRAINT,
        LoadDeviationCause.PERSONAL_CONSTRAINT,
        LoadDeviationCause.ATHLETE_CHOICE,
        LoadDeviationCause.FATIGUE,
        LoadDeviationCause.ILLNESS,
        LoadDeviationCause.INJURY,
        LoadDeviationCause.SPORT_EVENT,
        LoadDeviationCause.INCOMPLETE_DATA,
        LoadDeviationCause.UNKNOWN,
    ],
)
def test_all_deviation_causes_are_valid_for_significant_deviation(
    cause: LoadDeviationCause,
) -> None:
    result = contextualize_weekly_load_reconciliation(
        reconciliation=create_under_target_reconciliation(),
        cause=cause,
    )

    assert result.cause is cause
