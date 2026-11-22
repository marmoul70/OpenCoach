from datetime import date

from opencoach.schemas.coach import CoachWeeklyDebriefResponse


def test_weekly_debrief_response_accepts_unavailable_scores_and_ratios() -> None:
    response = CoachWeeklyDebriefResponse(
        week_start=date(2026, 11, 16),
        week_end=date(2026, 11, 22),
        verdict="unknown",
        adaptation_direction="observe",
        overall_score=None,
        adherence_score=None,
        duration_score=None,
        load_score=None,
        key_sessions_score=None,
        intensity_score=None,
        completion_ratio=None,
        duration_ratio=None,
        load_ratio=None,
        headline="Données insuffisantes",
        analysis="Les indicateurs ne peuvent pas être calculés.",
        strengths=[],
        warnings=[],
        planned_sessions=0,
        completed_sessions=0,
        skipped_sessions=0,
        supplementary_sessions=0,
        planned_duration_minutes=0,
        actual_duration_minutes=0,
        planned_load=0,
        actual_load=0,
    )

    assert response.intensity_score is None
    assert response.overall_score is None
    assert response.completion_ratio is None
