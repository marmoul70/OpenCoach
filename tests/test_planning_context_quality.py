from datetime import date

from opencoach.models import AthleteProfile
from opencoach.planning import (
    PlanningContext,
    assess_planning_context,
)


PLANNING_DATE = date(
    2026,
    8,
    22,
)


def create_context(
    athlete: AthleteProfile,
    *,
    primary_race=None,
    readiness=None,
    recent_load=None,
    recent_stats=None,
) -> PlanningContext:
        return PlanningContext(
            planning_date=PLANNING_DATE,
            athlete=athlete,
            primary_race=primary_race,
            training_races=(),
            readiness=readiness,
            recent_load=recent_load,
            recent_stats=recent_stats,
            constraints=(),
            constraints_end_date=date(
                2026,
                9,
                4,
            ),
        )


def create_plannable_athlete() -> AthleteProfile:
    athlete = AthleteProfile()

    athlete.training.weekly_sessions = 4
    athlete.training.weekly_duration_minutes = 360
    athlete.training.weekly_distance_km = 45.0
    athlete.training.available_days = [
        0,
        2,
        4,
        6,
    ]

    athlete.physiology.max_heart_rate = 181

    return athlete


def test_complete_training_profile_allows_general_planning() -> None:
    context = create_context(
        create_plannable_athlete()
    )

    assessment = assess_planning_context(
        context
    )

    assert assessment.general_planning is True
    assert assessment.has_blockers is False


def test_missing_weekly_sessions_blocks_general_planning() -> None:
    athlete = create_plannable_athlete()

    athlete.training.weekly_sessions = None

    assessment = assess_planning_context(
        create_context(athlete)
    )

    assert assessment.general_planning is False
    assert assessment.has_blockers is True

    assert (
        "Nombre de séances hebdomadaires non renseigné."
        in assessment.blockers
    )


def test_duration_or_distance_is_enough_for_reference_volume() -> None:
    athlete = create_plannable_athlete()

    athlete.training.weekly_duration_minutes = None
    athlete.training.weekly_distance_km = 45.0

    assessment = assess_planning_context(
        create_context(athlete)
    )

    assert assessment.general_planning is True


def test_missing_available_days_blocks_general_planning() -> None:
    athlete = create_plannable_athlete()

    athlete.training.available_days = []

    assessment = assess_planning_context(
        create_context(athlete)
    )

    assert assessment.general_planning is False

    assert (
        "Jours disponibles pour l'entraînement non renseignés."
        in assessment.blockers
    )


def test_missing_physiology_is_warning_not_blocker() -> None:
    athlete = create_plannable_athlete()

    athlete.physiology.max_heart_rate = None
    athlete.physiology.vma = None
    athlete.physiology.threshold_heart_rate_1 = None
    athlete.physiology.threshold_heart_rate_2 = None

    assessment = assess_planning_context(
        create_context(athlete)
    )

    assert assessment.general_planning is True

    assert (
        "Aucune référence physiologique d'intensité disponible."
        in assessment.warnings
    )


def test_missing_readiness_disables_daily_adaptation_only() -> None:
    athlete = create_plannable_athlete()

    assessment = assess_planning_context(
        create_context(
            athlete,
            readiness=None,
        )
    )

    assert assessment.general_planning is True
    assert assessment.daily_adaptation is False

    assert (
        "Readiness indisponible pour l'adaptation quotidienne."
        in assessment.warnings
    )


def test_missing_primary_race_disables_race_planning_only() -> None:
    athlete = create_plannable_athlete()

    assessment = assess_planning_context(
        create_context(
            athlete,
            primary_race=None,
        )
    )

    assert assessment.general_planning is True
    assert assessment.race_planning is False
