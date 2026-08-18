from datetime import date, timedelta

from sqlalchemy import select

from opencoach.database.models import AthleteProfile, User
from opencoach.database.repositories import (
    SqlTrainingSessionRepository,
)
from opencoach.database.session import SessionLocal
from opencoach.models import TrainingSession


LOCAL_USER_EMAIL = "local@opencoach.local"


def date_at_offset(offset: int) -> date:
    return date.today() + timedelta(days=offset)


SESSIONS = [
    TrainingSession(
        id=None,
        date=date_at_offset(-3),
        type="rest",
        title="Repos",
        description=(
            "Journée de récupération. "
            "Aucun entraînement prévu."
        ),
        duration_minutes=0,
        intensity="Repos",
        status="completed",
    ),
    TrainingSession(
        id=None,
        date=date_at_offset(-2),
        type="easy",
        title="Endurance fondamentale",
        description=(
            "Course facile en aisance respiratoire. "
            "Rester confortable et régulier."
        ),
        duration_minutes=50,
        distance_km=8,
        elevation_gain_m=100,
        intensity="Facile",
        heart_rate_zone="Z2",
        status="completed",
    ),
    TrainingSession(
        id=None,
        date=date_at_offset(-1),
        type="recovery",
        title="Récupération",
        description=(
            "Footing très léger destiné "
            "à favoriser la récupération."
        ),
        duration_minutes=40,
        distance_km=6,
        elevation_gain_m=50,
        intensity="Très facile",
        heart_rate_zone="Z1-Z2",
        status="completed",
    ),
    TrainingSession(
        id=None,
        date=date_at_offset(0),
        type="interval",
        title="VMA courte",
        description=(
            "Séance de fractionné destinée "
            "à travailler la vitesse maximale aérobie."
        ),
        duration_minutes=55,
        distance_km=8,
        elevation_gain_m=80,
        intensity="Soutenue",
        heart_rate_zone="Z4-Z5",
        status="planned",
    ),
    TrainingSession(
        id=None,
        date=date_at_offset(1),
        type="rest",
        title="Repos",
        description=(
            "Journée sans entraînement "
            "pour assimiler la charge."
        ),
        duration_minutes=0,
        intensity="Repos",
        status="planned",
    ),
    TrainingSession(
        id=None,
        date=date_at_offset(2),
        type="trail",
        title="Sortie longue trail",
        description=(
            "Sortie longue sur terrain vallonné "
            "avec travail de l'endurance spécifique trail."
        ),
        duration_minutes=135,
        distance_km=18,
        elevation_gain_m=850,
        intensity="Modérée",
        heart_rate_zone="Z2-Z3",
        status="planned",
    ),
    TrainingSession(
        id=None,
        date=date_at_offset(3),
        type="easy",
        title="Endurance",
        description=(
            "Footing d'endurance à intensité confortable."
        ),
        duration_minutes=60,
        distance_km=9,
        elevation_gain_m=120,
        intensity="Facile",
        heart_rate_zone="Z2",
        status="planned",
    ),
]


def main() -> None:
    with SessionLocal() as db:
        profile = db.scalar(
            select(AthleteProfile)
            .join(AthleteProfile.user)
            .where(
                User.email == LOCAL_USER_EMAIL,
            )
        )

        if profile is None:
            raise SystemExit(
                "Profil local OpenCoach introuvable."
            )

        repository = SqlTrainingSessionRepository(db)

        existing = repository.list_sessions_between(
            profile.id,
            date_at_offset(-3),
            date_at_offset(3),
        )

        if existing:
            raise SystemExit(
                "Des séances existent déjà pour cette période."
            )

        for session in SESSIONS:
            repository.save_session(
                profile.id,
                session,
            )

        print(
            f"{len(SESSIONS)} séances créées."
        )


if __name__ == "__main__":
    main()
