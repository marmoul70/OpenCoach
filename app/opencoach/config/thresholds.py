from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import tomllib


PROJECT_ROOT = Path(__file__).resolve().parents[3]

DEFAULT_THRESHOLDS_PATH = (
    PROJECT_ROOT
    / "config"
    / "thresholds.toml"
)


class ThresholdConfigurationError(RuntimeError):
    """Configuration des seuils OpenCoach invalide."""


@dataclass(frozen=True)
class ActivityMatchingThresholds:
    """Seuils du moteur de matching des activités."""

    best_match_score: float


@dataclass(frozen=True)
class ReadinessBaselineThresholds:
    """Paramètres de calcul de baseline Readiness."""

    window_days: int
    minimum_samples: int

@dataclass(frozen=True)
class ReadinessScoreThresholds:
    """Seuils de classification du score Readiness."""

    high_min: float
    good_min: float
    moderate_min: float
    low_min: float

    single_critical_cap: float
    multiple_critical_cap: float


@dataclass(frozen=True)
class ReadinessPenaltyThresholds:
    """Pénalités appliquées aux signaux de récupération."""

    warning: float
    critical: float


@dataclass(frozen=True)
class ReadinessDeviationThresholds:
    """Seuils warning/critical exprimés en pourcentage."""

    warning_percent: float
    critical_percent: float


@dataclass(frozen=True)
class ReadinessSleepDurationThresholds:
    """Seuils spécifiques à la durée du sommeil."""

    warning_percent: float
    critical_percent: float

    warning_hours: float
    critical_hours: float


@dataclass(frozen=True)
class ReadinessSleepScoreThresholds:
    """Seuils du score de sommeil."""

    warning_value: float
    critical_value: float


@dataclass(frozen=True)
class ReadinessTrainingLoadThresholds:
    """Seuils de balance CTL / ATL."""

    warning_balance: float
    critical_balance: float

@dataclass(frozen=True)
class ReadinessThresholds:
    """Configuration du moteur Daily Readiness."""

    baseline: ReadinessBaselineThresholds

    score: ReadinessScoreThresholds
    penalties: ReadinessPenaltyThresholds

    hrv: ReadinessDeviationThresholds
    resting_hr: ReadinessDeviationThresholds

    sleep_duration: ReadinessSleepDurationThresholds
    sleep_score: ReadinessSleepScoreThresholds

    training_load: ReadinessTrainingLoadThresholds

@dataclass(frozen=True)
class ThresholdSettings:
    """Ensemble des seuils configurables OpenCoach."""

    activity_matching: ActivityMatchingThresholds
    readiness: ReadinessThresholds


def load_threshold_settings(
    path: Path | None = None,
) -> ThresholdSettings:
    """Charge et valide les seuils OpenCoach."""

    config_path = (
        path
        if path is not None
        else DEFAULT_THRESHOLDS_PATH
    )

    if not config_path.exists():
        raise ThresholdConfigurationError(
            (
                "Fichier de seuils OpenCoach introuvable : "
                f"{config_path}"
            )
        )

    try:
        with config_path.open(
            "rb",
        ) as file:
            data = tomllib.load(file)

    except tomllib.TOMLDecodeError as exc:
        raise ThresholdConfigurationError(
            (
                "Le fichier de seuils OpenCoach "
                "contient un TOML invalide."
            )
        ) from exc

    try:
        activity_matching_data = data[
            "activity_matching"
        ]

        readiness_data = data[
            "readiness"
        ]

        baseline_data = readiness_data[
            "baseline"
        ]

        score_data = readiness_data[
            "score"
        ]

        penalties_data = readiness_data[
            "penalties"
        ]

        hrv_data = readiness_data[
            "hrv"
        ]

        resting_hr_data = readiness_data[
            "resting_hr"
        ]

        sleep_duration_data = readiness_data[
            "sleep_duration"
        ]

        sleep_score_data = readiness_data[
            "sleep_score"
        ]

        training_load_data = readiness_data[
            "training_load"
        ]

        settings = ThresholdSettings(
            activity_matching=(
                ActivityMatchingThresholds(
                    best_match_score=float(
                        activity_matching_data[
                            "best_match_score"
                        ]
                    ),
                )
            ),
            readiness=ReadinessThresholds(
                baseline=ReadinessBaselineThresholds(
                    window_days=int(
                        baseline_data[
                            "window_days"
                        ]
                    ),
                    minimum_samples=int(
                        baseline_data[
                            "minimum_samples"
                        ]
                    ),
                ),
                score=ReadinessScoreThresholds(
                    high_min=float(
                        score_data[
                            "high_min"
                        ]
                    ),
                    good_min=float(
                        score_data[
                            "good_min"
                        ]
                    ),
                    moderate_min=float(
                        score_data[
                            "moderate_min"
                        ]
                    ),
                    low_min=float(
                        score_data[
                            "low_min"
                        ]
                    ),
                    single_critical_cap=float(
                        score_data[
                            "single_critical_cap"
                        ]
                    ),
                    multiple_critical_cap=float(
                        score_data[
                            "multiple_critical_cap"
                        ]
                    ),
                ),
                penalties=ReadinessPenaltyThresholds(
                    warning=float(
                        penalties_data[
                            "warning"
                        ]
                    ),
                    critical=float(
                        penalties_data[
                            "critical"
                        ]
                    ),
                ),
                hrv=ReadinessDeviationThresholds(
                    warning_percent=float(
                        hrv_data[
                            "warning_percent"
                        ]
                    ),
                    critical_percent=float(
                        hrv_data[
                            "critical_percent"
                        ]
                    ),
                ),
                resting_hr=ReadinessDeviationThresholds(
                    warning_percent=float(
                        resting_hr_data[
                            "warning_percent"
                        ]
                    ),
                    critical_percent=float(
                        resting_hr_data[
                            "critical_percent"
                        ]
                    ),
                ),
                sleep_duration=ReadinessSleepDurationThresholds(
                    warning_percent=float(
                        sleep_duration_data[
                            "warning_percent"
                        ]
                    ),
                    critical_percent=float(
                        sleep_duration_data[
                            "critical_percent"
                        ]
                    ),
                    warning_hours=float(
                        sleep_duration_data[
                            "warning_hours"
                        ]
                    ),
                    critical_hours=float(
                        sleep_duration_data[
                            "critical_hours"
                        ]
                    ),
                ),
                sleep_score=ReadinessSleepScoreThresholds(
                    warning_value=float(
                        sleep_score_data[
                            "warning_value"
                        ]
                    ),
                    critical_value=float(
                        sleep_score_data[
                            "critical_value"
                        ]
                    ),
                ),
                training_load=ReadinessTrainingLoadThresholds(
                    warning_balance=float(
                        training_load_data[
                            "warning_balance"
                        ]
                    ),
                    critical_balance=float(
                        training_load_data[
                            "critical_balance"
                        ]
                    ),
                ),
            ),
        )

    except (
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        raise ThresholdConfigurationError(
            (
                "Le fichier de seuils OpenCoach "
                "est incomplet ou contient "
                "une valeur invalide."
            )
        ) from exc

    _validate_threshold_settings(
        settings,
    )

    return settings


@lru_cache(maxsize=1)
def get_threshold_settings() -> ThresholdSettings:
    """Retourne la configuration globale des seuils."""

    return load_threshold_settings()


def clear_threshold_settings_cache() -> None:
    """Vide le cache de configuration.

    Principalement utile pour les tests et, plus tard,
    pour le rechargement dynamique des réglages.
    """

    get_threshold_settings.cache_clear()


def _validate_threshold_settings(
    settings: ThresholdSettings,
) -> None:
    best_match_score = (
        settings
        .activity_matching
        .best_match_score
    )

    if not (
        0.0
        <= best_match_score
        <= 100.0
    ):
        raise ThresholdConfigurationError(
            (
                "activity_matching.best_match_score "
                "doit être compris entre 0 et 100."
            )
        )

    window_days = (
        settings
        .readiness
        .baseline
        .window_days
    )

    if window_days <= 0:
        raise ThresholdConfigurationError(
            (
                "readiness.baseline.window_days "
                "doit être supérieur à zéro."
            )
        )

    minimum_samples = (
        settings
        .readiness
        .baseline
        .minimum_samples
    )

    if minimum_samples <= 0:
        raise ThresholdConfigurationError(
            (
                "readiness.baseline.minimum_samples "
                "doit être supérieur à zéro."
            )
        )

    if minimum_samples > window_days:
        raise ThresholdConfigurationError(
            (
                "readiness.baseline.minimum_samples "
                "ne peut pas dépasser window_days."
            )
        )
