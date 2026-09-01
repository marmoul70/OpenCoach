"""Envoie le rappel de la séance prévue le lendemain."""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import select

from opencoach.coaching.tomorrow_session_reminder import (
    build_tomorrow_session_reminder,
)
from opencoach.database.models import (
    AthleteProfile,
    User,
)
from opencoach.database.repositories.sql_training_session import (
    SqlTrainingSessionRepository,
)
from opencoach.database.session import SessionLocal
from opencoach.integrations.open_meteo.client import (
    OpenMeteoClient,
    OpenMeteoError,
)
from opencoach.services.push_notification import (
    PushNotificationService,
)
from opencoach.weather.training_advisory import (
    TrainingWeatherAdvice,
    build_training_weather_advice,
)


LOCAL_USER_EMAIL = "local@opencoach.local"


def _load_local_profile(
    database,
) -> AthleteProfile | None:
    return database.scalar(
        select(
            AthleteProfile
        )
        .join(
            AthleteProfile.user
        )
        .where(
            User.email
            == LOCAL_USER_EMAIL
        )
    )


def _weather_advice(
    profile: AthleteProfile,
    *,
    target_date: date,
) -> TrainingWeatherAdvice | None:
    if (
        profile.latitude is None
        or profile.longitude is None
    ):
        print(
            "[INFO] Localisation absente : "
            "rappel envoyé sans météo."
        )

        return None

    try:
        forecast = (
            OpenMeteoClient()
            .fetch_forecast(
                latitude=(
                    profile.latitude
                ),
                longitude=(
                    profile.longitude
                ),
            )
        )

    except OpenMeteoError as exc:
        print(
            "[AVERTISSEMENT] "
            "Météo indisponible : "
            f"{exc}"
        )

        return None

    return (
        build_training_weather_advice(
            forecast,
            target_date=target_date,
        )
    )


def main() -> int:
    tomorrow = (
        date.today()
        + timedelta(
            days=1,
        )
    )

    with SessionLocal() as database:
        profile = _load_local_profile(
            database
        )

        if profile is None:
            print(
                "[INFO] Aucun profil "
                "athlète local."
            )

            return 0

        repository = (
            SqlTrainingSessionRepository(
                database
            )
        )

        sessions = (
            repository
            .list_sessions_between(
                profile.id,
                tomorrow,
                tomorrow,
            )
        )

        planned_sessions = [
            session
            for session in sessions
            if session.status
            == "planned"
        ]

        if not planned_sessions:
            print(
                "[INFO] Aucune séance "
                "planifiée le "
                f"{tomorrow.isoformat()}."
            )

            return 0

        advice = _weather_advice(
            profile,
            target_date=tomorrow,
        )

        push_service = (
            PushNotificationService(
                database
            )
        )

        sent = 0
        failed = 0
        removed = 0

        for training_session in (
            planned_sessions
        ):
            reminder = (
                build_tomorrow_session_reminder(
                    training_session,
                    weather_advice=advice,
                )
            )

            report = (
                push_service
                .send_training_reminder(
                    title=reminder.title,
                    body=reminder.body,
                    url=reminder.url,
                )
            )

            sent += report.sent
            failed += report.failed
            removed += report.removed

            print(
                "[OK] Rappel :",
                training_session.title,
            )

            if (
                advice is not None
                and advice.message
            ):
                print(
                    "[INFO] Conseil météo :",
                    advice.message,
                )

        print()
        print(
            "Envoyées   :",
            sent,
        )
        print(
            "Échecs     :",
            failed,
        )
        print(
            "Supprimées :",
            removed,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
