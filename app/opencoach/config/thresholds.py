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
class ReadinessContextFatigueThresholds:
    """Seuils de fatigue subjective."""

    warning_min: int
    critical_min: int


@dataclass(frozen=True)
class ReadinessContextPainThresholds:
    """Seuils de douleur subjective."""

    warning_min: int
    critical_min: int


@dataclass(frozen=True)
class ReadinessContextStatusThresholds:
    """Niveaux associés à un état subjectif."""

    mild_level: str
    significant_level: str

@dataclass(frozen=True)
class ReadinessContextMotivationThresholds:
    """Seuils liés à la motivation."""

    low_max: int

@dataclass(frozen=True)
class ReadinessContextCapThresholds:
    """Plafonds de Readiness liés au contexte subjectif."""

    significant_treatment: float
    significant_illness: float
    critical_pain: float


@dataclass(frozen=True)
class ReadinessContextThresholds:
    """Configuration du contexte subjectif quotidien."""

    fatigue: ReadinessContextFatigueThresholds
    pain: ReadinessContextPainThresholds

    illness: ReadinessContextStatusThresholds
    treatment: ReadinessContextStatusThresholds

    caps: ReadinessContextCapThresholds

    motivation: ReadinessContextMotivationThresholds

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

    context: ReadinessContextThresholds

@dataclass(frozen=True)
class CoachDecisionReadinessThresholds:
    """Seuils de décision basés sur le Daily Readiness."""

    keep_min: float
    reduce_min: float
    replace_min: float


@dataclass(frozen=True)
class CoachDecisionReductionThresholds:
    """Facteurs de réduction d'une séance."""

    duration_factor: float
    intensity_factor: float


@dataclass(frozen=True)
class CoachDecisionConstraintThresholds:
    """Paramètres liés aux contraintes d'entraînement."""

    avoid_high_intensity_duration_factor: float
    recovery_max_duration_minutes: int


@dataclass(frozen=True)
class CoachDecisionThresholds:
    """Configuration du Coach Decision Engine."""

    readiness: CoachDecisionReadinessThresholds
    reduction: CoachDecisionReductionThresholds
    constraints: CoachDecisionConstraintThresholds

@dataclass(frozen=True)
class ThresholdSettings:
    """Ensemble des seuils configurables OpenCoach."""

    activity_matching: ActivityMatchingThresholds
    readiness: ReadinessThresholds
    coach_decision: CoachDecisionThresholds

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

        coach_decision_data = data[
            "coach_decision"
        ]

        coach_readiness_data = coach_decision_data[
            "readiness"
        ]

        coach_reduction_data = coach_decision_data[
            "reduction"
        ]

        coach_constraints_data = coach_decision_data[
            "constraints"
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

        context_data = readiness_data[
            "context"
        ]

        context_fatigue_data = context_data[
            "fatigue"
        ]

        context_pain_data = context_data[
            "pain"
        ]

        context_illness_data = context_data[
            "illness"
        ]

        context_treatment_data = context_data[
            "treatment"
        ]

        context_motivation_data = context_data[
            "motivation"
        ]

        context_caps_data = context_data[
            "caps"
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
                context=ReadinessContextThresholds(
                    fatigue=ReadinessContextFatigueThresholds(
                        warning_min=int(
                            context_fatigue_data[
                                "warning_min"
                            ]
                        ),
                        critical_min=int(
                            context_fatigue_data[
                                "critical_min"
                            ]
                        ),
                    ),
                    motivation=ReadinessContextMotivationThresholds(
                        low_max=int(
                            context_motivation_data[
                                "low_max"
                            ]
                        ),
                    ),
                    pain=ReadinessContextPainThresholds(
                        warning_min=int(
                            context_pain_data[
                                "warning_min"
                            ]
                        ),
                        critical_min=int(
                            context_pain_data[
                                "critical_min"
                            ]
                        ),
                    ),
                    illness=ReadinessContextStatusThresholds(
                        mild_level=str(
                            context_illness_data[
                                "mild_level"
                            ]
                        ),
                        significant_level=str(
                            context_illness_data[
                                "significant_level"
                            ]
                        ),
                    ),
                    treatment=ReadinessContextStatusThresholds(
                        mild_level=str(
                            context_treatment_data[
                                "mild_level"
                            ]
                        ),
                        significant_level=str(
                            context_treatment_data[
                                "significant_level"
                            ]
                        ),
                    ),
                    caps=ReadinessContextCapThresholds(
                        significant_treatment=float(
                            context_caps_data[
                                "significant_treatment"
                            ]
                        ),
                        significant_illness=float(
                            context_caps_data[
                                "significant_illness"
                            ]
                        ),
                        critical_pain=float(
                            context_caps_data[
                                "critical_pain"
                            ]
                        ),
                    ),
                ),
            ),
            coach_decision=CoachDecisionThresholds(
                readiness=CoachDecisionReadinessThresholds(
                    keep_min=float(
                        coach_readiness_data[
                            "keep_min"
                        ]
                    ),
                    reduce_min=float(
                        coach_readiness_data[
                            "reduce_min"
                        ]
                    ),
                    replace_min=float(
                        coach_readiness_data[
                            "replace_min"
                        ]
                    ),
                ),
                reduction=CoachDecisionReductionThresholds(
                    duration_factor=float(
                        coach_reduction_data[
                            "duration_factor"
                        ]
                    ),
                    intensity_factor=float(
                        coach_reduction_data[
                            "intensity_factor"
                        ]
                    ),
                ),
                constraints=CoachDecisionConstraintThresholds(
                    avoid_high_intensity_duration_factor=float(
                        coach_constraints_data[
                            "avoid_high_intensity_duration_factor"
                        ]
                    ),
                    recovery_max_duration_minutes=int(
                        coach_constraints_data[
                            "recovery_max_duration_minutes"
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

    context = (
        settings
        .readiness
        .context
    )

    if not (
        1
        <= context.fatigue.warning_min
        <= 5
    ):
        raise ThresholdConfigurationError(
            (
                "readiness.context.fatigue.warning_min "
                "doit être compris entre 1 et 5."
            )
        )

    if not (
        1
        <= context.fatigue.critical_min
        <= 5
    ):
        raise ThresholdConfigurationError(
            (
                "readiness.context.fatigue.critical_min "
                "doit être compris entre 1 et 5."
            )
        )

    if (
        context.fatigue.warning_min
        >= context.fatigue.critical_min
    ):
        raise ThresholdConfigurationError(
            (
                "readiness.context.fatigue.warning_min "
                "doit être inférieur à critical_min."
            )
        )

    if not (
        0
        <= context.pain.warning_min
        <= 10
    ):
        raise ThresholdConfigurationError(
            (
                "readiness.context.pain.warning_min "
                "doit être compris entre 0 et 10."
            )
        )

    if not (
        0
        <= context.pain.critical_min
        <= 10
    ):
        raise ThresholdConfigurationError(
            (
                "readiness.context.pain.critical_min "
                "doit être compris entre 0 et 10."
            )
        )

    if (
        context.pain.warning_min
        >= context.pain.critical_min
    ):
        raise ThresholdConfigurationError(
            (
                "readiness.context.pain.warning_min "
                "doit être inférieur à critical_min."
            )
        )

    valid_signal_levels = {
        "normal",
        "warning",
        "critical",
    }

    for name, status in (
        (
            "illness",
            context.illness,
        ),
        (
            "treatment",
            context.treatment,
        ),
    ):
        if (
            status.mild_level
            not in valid_signal_levels
        ):
            raise ThresholdConfigurationError(
                (
                    f"readiness.context.{name}.mild_level "
                    "contient un niveau invalide."
                )
            )

        if (
            status.significant_level
            not in valid_signal_levels
        ):
            raise ThresholdConfigurationError(
                (
                    f"readiness.context.{name}."
                    "significant_level contient "
                    "un niveau invalide."
                )
            )

    for name, value in (
        (
            "significant_treatment",
            context.caps.significant_treatment,
        ),
        (
            "significant_illness",
            context.caps.significant_illness,
        ),
        (
            "critical_pain",
            context.caps.critical_pain,
        ),
    ):
        if not (
            0.0
            <= value
            <= 100.0
        ):
            raise ThresholdConfigurationError(
                (
                    f"readiness.context.caps.{name} "
                    "doit être compris entre 0 et 100."
                )
            )
    coach_decision = (
        settings
        .coach_decision
    )

    keep_min = (
        coach_decision
        .readiness
        .keep_min
    )

    reduce_min = (
        coach_decision
        .readiness
        .reduce_min
    )

    replace_min = (
        coach_decision
        .readiness
        .replace_min
    )

    if not (
        0.0
        <= replace_min
        < reduce_min
        < keep_min
        <= 100.0
    ):
        raise ThresholdConfigurationError(
            (
                "Les seuils coach_decision.readiness "
                "doivent respecter : "
                "0 <= replace_min < reduce_min "
                "< keep_min <= 100."
            )
        )

    duration_factor = (
        coach_decision
        .reduction
        .duration_factor
    )

    if not (
        0.0
        < duration_factor
        <= 1.0
    ):
        raise ThresholdConfigurationError(
            (
                "coach_decision.reduction."
                "duration_factor doit être "
                "compris entre 0 exclu et 1."
            )
        )

    intensity_factor = (
        coach_decision
        .reduction
        .intensity_factor
    )

    if not (
        0.0
        < intensity_factor
        <= 1.0
    ):
        raise ThresholdConfigurationError(
            (
                "coach_decision.reduction."
                "intensity_factor doit être "
                "compris entre 0 exclu et 1."
            )
        )

    constraint_factor = (
        coach_decision
        .constraints
        .avoid_high_intensity_duration_factor
    )

    if not (
        0.0
        < constraint_factor
        <= 1.0
    ):
        raise ThresholdConfigurationError(
            (
                "coach_decision.constraints."
                "avoid_high_intensity_duration_factor "
                "doit être compris entre 0 exclu et 1."
            )
        )

    if (
        coach_decision
        .constraints
        .recovery_max_duration_minutes
        <= 0
    ):
        raise ThresholdConfigurationError(
            (
                "coach_decision.constraints."
                "recovery_max_duration_minutes "
                "doit être supérieur à zéro."
            )
        )