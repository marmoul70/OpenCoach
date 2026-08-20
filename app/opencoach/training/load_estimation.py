from opencoach.models import TrainingSession


CANONICAL_INTENSITIES = (
    "very_easy",
    "easy",
    "moderate",
    "hard",
    "very_hard",
)


INTENSITY_LOAD_FACTORS = {
    "very_easy": 0.30,
    "easy": 0.45,
    "moderate": 0.60,
    "hard": 0.80,
    "very_hard": 1.00,
}


INTENSITY_ALIASES = {
    # Anciennes valeurs françaises OpenCoach
    "très facile": "very_easy",
    "tres facile": "very_easy",
    "facile": "easy",
    "modérée": "moderate",
    "moderee": "moderate",
    "soutenue": "hard",
    "élevée": "very_hard",
    "elevee": "very_hard",

    # Anciennes valeurs internes Coach
    "recovery": "very_easy",
    "very easy": "very_easy",
    "very_easy": "very_easy",
    "easy": "easy",
    "moderate": "moderate",
    "hard": "hard",
    "high": "very_hard",
    "very hard": "very_hard",
    "very_hard": "very_hard",
}


def normalize_intensity(
    intensity: str | None,
) -> str:
    """Normalise une intensité vers le vocabulaire canonique OpenCoach."""

    if intensity is None:
        return "easy"

    value = intensity.strip()

    if not value:
        return "easy"

    if value in CANONICAL_INTENSITIES:
        return value

    normalized = INTENSITY_ALIASES.get(
        value.casefold(),
    )

    if normalized is not None:
        return normalized

    raise ValueError(
        f"Intensité OpenCoach inconnue : {intensity!r}."
    )


def get_intensity_load_factor(
    intensity: str | None,
) -> float:
    """Retourne le coefficient de charge associé à une intensité."""

    normalized_intensity = normalize_intensity(
        intensity,
    )

    return INTENSITY_LOAD_FACTORS[
        normalized_intensity
    ]


def estimate_load(
    *,
    duration_minutes: int,
    intensity: str | None,
) -> float:
    """Estime une charge à partir de la durée et de l'intensité."""

    if duration_minutes <= 0:
        return 0.0

    factor = get_intensity_load_factor(
        intensity,
    )

    return round(
        duration_minutes * factor,
        2,
    )


def estimate_prescribed_load(
    session: TrainingSession,
) -> float:
    """Estime la charge théorique d'une séance prescrite."""

    if session.type == "rest":
        return 0.0

    return estimate_load(
        duration_minutes=session.duration_minutes,
        intensity=session.intensity,
    )


def estimate_session_load(
    session: TrainingSession,
) -> float:
    """Estime la charge d'une séance réellement effectuée manuellement."""

    if (
        session.status != "completed"
        or session.activity_id is not None
    ):
        return 0.0

    return estimate_prescribed_load(
        session,
    )