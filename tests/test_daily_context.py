from datetime import date

from opencoach.models import DailyContext


def test_daily_context_can_be_created() -> None:
    context = DailyContext(
        date=date(2026, 8, 18),
        fatigue_subjective=4,
        pain_level=2,
        illness_status="none",
        treatment_impact="significant",
        motivation=2,
        notes="Fatigue importante aujourd'hui.",
    )

    assert context.date == date(2026, 8, 18)
    assert context.fatigue_subjective == 4
    assert context.pain_level == 2
    assert context.illness_status == "none"
    assert context.treatment_impact == "significant"
    assert context.motivation == 2
    assert context.notes == "Fatigue importante aujourd'hui."


def test_daily_context_has_safe_defaults() -> None:
    context = DailyContext(
        date=date(2026, 8, 18),
        fatigue_subjective=2,
        pain_level=0,
    )

    assert context.illness_status == "none"
    assert context.treatment_impact == "none"
    assert context.motivation == 3
    assert context.notes is None
