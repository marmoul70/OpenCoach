from opencoach.planning.trajectory.adjustment import (
    LoadAdjustment,
    ProgressionAdjustment,
)
from opencoach.planning.weekly.load_reconciliation import (
    reconcile_weekly_load,
)
from opencoach.planning.weekly.load_reconciliation_context import (
    LoadDeviationCause,
    contextualize_weekly_load_reconciliation,
)
from opencoach.planning.weekly.load_reconciliation_policy import (
    build_reconciliation_adjustment,
)


def build_adjustment(
    *,
    planned_load: float,
    actual_load: float,
    cause: LoadDeviationCause | None = None,
    athlete_imposed: bool = False,
):
    reconciliation = reconcile_weekly_load(
        planned_load=planned_load,
        actual_load=actual_load,
    )

    context = contextualize_weekly_load_reconciliation(
        reconciliation=reconciliation,
        cause=cause,
        athlete_imposed=athlete_imposed,
    )

    return build_reconciliation_adjustment(
        context
    )


def test_on_target_keeps_normal_trajectory() -> None:
    result = build_adjustment(
        planned_load=500.0,
        actual_load=490.0,
    )

    assert result.load is LoadAdjustment.MAINTAIN

    assert (
        result.progression
        is ProgressionAdjustment.CONTINUE
    )


def test_professional_constraint_does_not_become_fatigue() -> None:
    result = build_adjustment(
        planned_load=500.0,
        actual_load=350.0,
        cause=LoadDeviationCause.PROFESSIONAL_CONSTRAINT,
        athlete_imposed=True,
    )

    assert result.load is LoadAdjustment.MAINTAIN

    assert (
        result.progression
        is ProgressionAdjustment.CONTINUE
    )

    assert result.allow_schedule_compression is True
    assert result.athlete_override_allowed is True


def test_personal_constraint_preserves_trajectory() -> None:
    result = build_adjustment(
        planned_load=500.0,
        actual_load=350.0,
        cause=LoadDeviationCause.PERSONAL_CONSTRAINT,
        athlete_imposed=True,
    )

    assert result.load is LoadAdjustment.MAINTAIN

    assert (
        result.progression
        is ProgressionAdjustment.CONTINUE
    )


def test_athlete_choice_preserves_final_authority() -> None:
    result = build_adjustment(
        planned_load=500.0,
        actual_load=350.0,
        cause=LoadDeviationCause.ATHLETE_CHOICE,
        athlete_imposed=True,
    )

    assert result.athlete_override_allowed is True

    assert result.load is LoadAdjustment.MAINTAIN


def test_incomplete_data_does_not_modify_trajectory() -> None:
    result = build_adjustment(
        planned_load=500.0,
        actual_load=350.0,
        cause=LoadDeviationCause.INCOMPLETE_DATA,
    )

    assert result.load is LoadAdjustment.MAINTAIN

    assert (
        result.progression
        is ProgressionAdjustment.CONTINUE
    )


def test_underload_with_fatigue_slows_progression() -> None:
    result = build_adjustment(
        planned_load=500.0,
        actual_load=400.0,
        cause=LoadDeviationCause.FATIGUE,
    )

    assert result.load is LoadAdjustment.REDUCE_SLIGHTLY

    assert result.progression is ProgressionAdjustment.SLOW

    assert result.allow_schedule_compression is False


def test_strong_underload_with_fatigue_pauses_progression() -> None:
    result = build_adjustment(
        planned_load=500.0,
        actual_load=300.0,
        cause=LoadDeviationCause.FATIGUE,
    )

    assert result.load is LoadAdjustment.REDUCE

    assert result.progression is ProgressionAdjustment.PAUSE


def test_underload_with_illness_pauses_progression() -> None:
    result = build_adjustment(
        planned_load=500.0,
        actual_load=400.0,
        cause=LoadDeviationCause.ILLNESS,
    )

    assert result.load is LoadAdjustment.REDUCE

    assert result.progression is ProgressionAdjustment.PAUSE


def test_strong_underload_with_illness_reduces_strongly() -> None:
    result = build_adjustment(
        planned_load=500.0,
        actual_load=300.0,
        cause=LoadDeviationCause.ILLNESS,
    )

    assert result.load is LoadAdjustment.REDUCE_STRONGLY

    assert result.progression is ProgressionAdjustment.PAUSE

    assert result.requires_return_to_training is False


def test_underload_with_injury_protects_trajectory() -> None:
    result = build_adjustment(
        planned_load=500.0,
        actual_load=400.0,
        cause=LoadDeviationCause.INJURY,
    )

    assert result.load is LoadAdjustment.REDUCE_STRONGLY

    assert result.progression is ProgressionAdjustment.PAUSE

    assert result.allow_schedule_compression is False


def test_strong_underload_with_injury_requires_rebuild() -> None:
    result = build_adjustment(
        planned_load=500.0,
        actual_load=300.0,
        cause=LoadDeviationCause.INJURY,
    )

    assert result.load is LoadAdjustment.SUSPEND

    assert result.progression is ProgressionAdjustment.REBUILD

    assert result.requires_return_to_training is True


def test_overload_protects_next_week() -> None:
    result = build_adjustment(
        planned_load=500.0,
        actual_load=600.0,
        cause=LoadDeviationCause.UNKNOWN,
    )

    assert result.load is LoadAdjustment.REDUCE_SLIGHTLY

    assert (
        result.progression
        is ProgressionAdjustment.CONTINUE
    )

    assert result.allow_schedule_compression is False


def test_strong_overload_slows_next_progression() -> None:
    result = build_adjustment(
        planned_load=500.0,
        actual_load=700.0,
        cause=LoadDeviationCause.UNKNOWN,
    )

    assert result.load is LoadAdjustment.REDUCE

    assert result.progression is ProgressionAdjustment.SLOW

    assert result.allow_schedule_compression is False


def test_sport_event_does_not_duplicate_event_engine() -> None:
    result = build_adjustment(
        planned_load=500.0,
        actual_load=400.0,
        cause=LoadDeviationCause.SPORT_EVENT,
    )

    assert result.load is LoadAdjustment.MAINTAIN

    assert (
        result.progression
        is ProgressionAdjustment.CONTINUE
    )


def test_unknown_moderate_underload_keeps_trajectory() -> None:
    result = build_adjustment(
        planned_load=500.0,
        actual_load=400.0,
        cause=LoadDeviationCause.UNKNOWN,
    )

    assert result.load is LoadAdjustment.MAINTAIN

    assert (
        result.progression
        is ProgressionAdjustment.CONTINUE
    )


def test_unknown_strong_underload_slows_cautiously() -> None:
    result = build_adjustment(
        planned_load=500.0,
        actual_load=300.0,
        cause=LoadDeviationCause.UNKNOWN,
    )

    assert result.load is LoadAdjustment.REDUCE_SLIGHTLY

    assert result.progression is ProgressionAdjustment.SLOW


def test_all_decisions_preserve_athlete_override() -> None:
    cases = (
        (500.0, 490.0, None),
        (
            500.0,
            400.0,
            LoadDeviationCause.FATIGUE,
        ),
        (
            500.0,
            300.0,
            LoadDeviationCause.INJURY,
        ),
        (
            500.0,
            700.0,
            LoadDeviationCause.UNKNOWN,
        ),
    )

    for planned, actual, cause in cases:
        result = build_adjustment(
            planned_load=planned,
            actual_load=actual,
            cause=cause,
        )

        assert result.athlete_override_allowed is True
