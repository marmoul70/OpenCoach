"""Envoie les rappels des séances prévues le lendemain."""

from __future__ import annotations

from datetime import date, timedelta
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select

from opencoach.api.coros import (
    CorosWorkoutPushRequest,
    push_training_session_to_coros,
)
from opencoach.coaching.tomorrow_session_reminder import (
    build_tomorrow_session_reminder,
)
from opencoach.database.models import (
    AthleteProfile,
    IntegrationConnection,
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


def _load_active_profiles(
    database,
) -> list[AthleteProfile]:
    """Charge les profils appartenant aux utilisateurs actifs."""

    statement = (
        select(AthleteProfile)
        .join(
            AthleteProfile.user
        )
        .where(
            User.active.is_(True)
        )
        .order_by(
            AthleteProfile.id.asc()
        )
    )

    return list(
        database.scalars(
            statement
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


def _sync_session_to_coros(
    database,
    *,
    athlete_profile_id: UUID,
    session_id: UUID,
) -> str | None:
    """Synchronise la séance via le même flux sécurisé que l'envoi manuel.

    Aucun envoi n'est tenté si COROS n'est pas activé pour le profil.
    Les états incertains restent protégés par les contrôles de l'API : le
    rappel ne confirme jamais une création COROS dont le résultat est ambigu.
    """
    connection = database.scalar(
        select(IntegrationConnection).where(
            IntegrationConnection.athlete_profile_id == athlete_profile_id,
            IntegrationConnection.provider == "coros",
        )
    )
    if connection is None or not connection.enabled:
        return None

    try:
        result = push_training_session_to_coros(
            session_id=session_id,
            payload=CorosWorkoutPushRequest(),
            athlete_profile_id=athlete_profile_id,
            db=database,
        )
    except HTTPException as exc:
        detail = exc.detail
        if isinstance(detail, str) and detail.strip():
            return f"Synchronisation COROS non effectuée : {detail.strip()}"
        return (
            "Synchronisation COROS non effectuée : "
            f"erreur HTTP {exc.status_code}."
        )
    except Exception as exc:
        # La notification de rappel doit rester envoyée même si COROS est
        # indisponible. Le détail est journalisé sans exposer de secret.
        print(
            "[AVERTISSEMENT] Synchronisation COROS impossible "
            f"pour la séance {session_id} : {exc}"
        )
        return (
            "Synchronisation COROS indisponible. "
            "Consulte OpenCoach avant ta séance."
        )

    message = result.get("message") if isinstance(result, dict) else None
    if isinstance(message, str) and message.strip():
        return f"COROS : {message.strip()}"
    if isinstance(result, dict) and result.get("status") == "synced":
        return "COROS : séance synchronisée."
    return "Synchronisation COROS non confirmée."


def main() -> int:
    tomorrow = (
        date.today()
        + timedelta(
            days=1,
        )
    )

    total_sent = 0
    total_failed = 0
    total_removed = 0
    profile_failures = 0

    with SessionLocal() as database:
        profiles = (
            _load_active_profiles(
                database
            )
        )

        if not profiles:
            print(
                "[INFO] Aucun profil "
                "athlète actif."
            )

            return 0

        print(
            "[INFO] Profils à traiter : "
            f"{len(profiles)}."
        )

        repository = (
            SqlTrainingSessionRepository(
                database
            )
        )

        push_service = (
            PushNotificationService(
                database
            )
        )

        for profile in profiles:
            user_id = (
                profile.user_id
            )

            print()
            print(
                "[INFO] Traitement du profil "
                f"{profile.id}."
            )

            try:
                sessions = (
                    repository
                    .list_sessions_between(
                        profile.id,
                        tomorrow,
                        tomorrow,
                    )
                )

                planned_sessions = [
                    training_session
                    for training_session
                    in sessions
                    if (
                        training_session.status
                        == "planned"
                    )
                ]

                if not planned_sessions:
                    print(
                        "[INFO] Aucune séance "
                        "planifiée le "
                        f"{tomorrow.isoformat()}."
                    )

                    continue

                advice = (
                    _weather_advice(
                        profile,
                        target_date=tomorrow,
                    )
                )

                for training_session in (
                    planned_sessions
                ):
                    coros_message = _sync_session_to_coros(
                        database,
                        athlete_profile_id=profile.id,
                        session_id=training_session.id,
                    )
                    reminder = (
                        build_tomorrow_session_reminder(
                            training_session,
                            weather_advice=advice,
                        )
                    )
                    reminder_body = reminder.body
                    if coros_message:
                        reminder_body += " " + coros_message

                    report = (
                        push_service
                        .send_training_reminder(
                            user_id=user_id,
                            title=reminder.title,
                            body=reminder_body,
                            url=reminder.url,
                        )
                    )

                    total_sent += (
                        report.sent
                    )

                    total_failed += (
                        report.failed
                    )

                    total_removed += (
                        report.removed
                    )

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

            except Exception as exc:
                profile_failures += 1

                print(
                    "[ERREUR] Profil "
                    f"{profile.id} : {exc}"
                )

                continue

        print()
        print("=" * 72)
        print(" BILAN RAPPELS")
        print("=" * 72)

        print(
            "Envoyées   :",
            total_sent,
        )

        print(
            "Échecs     :",
            total_failed,
        )

        print(
            "Supprimées :",
            total_removed,
        )

        print(
            "Profils KO  :",
            profile_failures,
        )

    if profile_failures:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
