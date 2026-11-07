from datetime import date
from types import SimpleNamespace

from opencoach.ai.context import build_athlete_context


def test_build_athlete_context_includes_only_selected_deterministic_facts() -> None:
    context = SimpleNamespace(
        planning_date=date(2026, 11, 7),
        athlete=SimpleNamespace(
            training=SimpleNamespace(
                sport_disciplines=["trail_running"],
                experience="advanced",
                weekly_sessions=4,
                weekly_duration_minutes=300,
                weekly_distance_km=40.0,
            ),
            physiology=SimpleNamespace(
                vma=15.0,
                max_heart_rate=181,
                resting_heart_rate=48,
            ),
        ),
        recent_stats=SimpleNamespace(
            start_date=date(2026, 10, 10),
            end_date=date(2026, 11, 6),
            sessions_count=12,
            total_duration_minutes=900,
            total_distance_km=120.5,
            total_elevation_gain_m=3200,
            total_load=850.0,
        ),
        recent_load=SimpleNamespace(
            analyzed_days=7,
            above_plan_days=1,
            on_plan_days=4,
            below_plan_days=2,
            planning_coverage_ratio=0.8,
        ),
        readiness=SimpleNamespace(
            readiness=SimpleNamespace(
                level="good",
                score=82.0,
                training_constraints=(),
            ),
            data_status="fresh",
            source_date=date(2026, 11, 7),
            provider="coros",
        ),
        primary_race=SimpleNamespace(
            name="Trail test",
            date=date(2026, 12, 1),
            distance_km=25.0,
            elevation_gain_m=1200,
        ),
        constraints=(),
    )

    result = build_athlete_context(context)

    assert "VMA enregistrée : 15.0 km/h." in result
    assert "120.5 km" in result
    assert "Disponibilité quotidienne calculée : good" in result
    assert "Trail test" in result
    assert "données personnelles" not in result.lower()
    assert "ne peux modifier" in result


def test_build_athlete_context_handles_missing_optional_data() -> None:
    context = SimpleNamespace(
        planning_date=date(2026, 11, 7),
        athlete=SimpleNamespace(
            training=SimpleNamespace(
                sport_disciplines=[],
                experience="beginner",
                weekly_sessions=None,
                weekly_duration_minutes=None,
                weekly_distance_km=None,
            ),
            physiology=SimpleNamespace(
                vma=None,
                max_heart_rate=None,
                resting_heart_rate=None,
            ),
        ),
        recent_stats=None,
        recent_load=None,
        readiness=None,
        primary_race=None,
        constraints=(),
    )

    result = build_athlete_context(context)

    assert "aucune donnée exploitable" in result
    assert "Aucune course principale future" in result
