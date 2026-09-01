from datetime import date
from uuid import uuid4

from opencoach.coaching.tomorrow_session_reminder import (
    build_tomorrow_session_reminder,
)
from opencoach.models import (
    TrainingSession,
)
from opencoach.weather.training_advisory import (
    TrainingWeatherAdvice,
)


def create_session(
    *,
    title: str = "Endurance fondamentale",
    session_type: str = "easy",
):
    return TrainingSession(
        id=uuid4(),
        date=date(
            2026,
            9,
            2,
        ),
        type=session_type,
        sport_type="Run",
        title=title,
        description="",
        duration_minutes=50,
        distance_km=None,
        elevation_gain_m=None,
        intensity="easy",
        heart_rate_zone=None,
        prescription=None,
        status="planned",
        activity_id=None,
    )


def test_easy_session_message():
    session = (
        create_session()
    )

    reminder = (
        build_tomorrow_session_reminder(
            session
        )
    )

    assert (
        "séance EF"
        in reminder.body
    )

    assert (
        "50 min"
        in reminder.body
    )

    assert (
        str(session.id)
        in reminder.url
    )


def test_interval_session_message():
    session = create_session(
        title="Fractionné court",
        session_type="intervals",
    )

    reminder = (
        build_tomorrow_session_reminder(
            session
        )
    )

    assert (
        "fractionnée"
        in reminder.body
    )


def test_weather_advice_is_appended():
    session = (
        create_session()
    )

    reminder = (
        build_tomorrow_session_reminder(
            session,
            weather_advice=(
                TrainingWeatherAdvice(
                    message=(
                        "Pluie annoncée "
                        "l’après-midi. "
                        "Privilégie le matin."
                    ),
                    preferred_period=(
                        "matin"
                    ),
                )
            ),
        )
    )

    assert (
        "Pluie annoncée"
        in reminder.body
    )
