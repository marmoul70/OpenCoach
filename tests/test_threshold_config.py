from pathlib import Path

import pytest

from opencoach.config import (
    ThresholdConfigurationError,
    load_threshold_settings,
)

def test_threshold_settings_load_project_config() -> None:
    settings = load_threshold_settings()

    assert settings.activity_matching.best_match_score == 75.0

    assert settings.readiness.baseline.window_days == 14
    assert settings.readiness.baseline.minimum_samples == 7

    assert settings.readiness.score.high_min == 85.0
    assert settings.readiness.score.good_min == 70.0
    assert settings.readiness.score.moderate_min == 50.0
    assert settings.readiness.score.low_min == 30.0

    assert settings.readiness.penalties.warning == 10.0
    assert settings.readiness.penalties.critical == 25.0

    assert settings.readiness.hrv.warning_percent == -10.0
    assert settings.readiness.hrv.critical_percent == -20.0

    assert settings.readiness.resting_hr.warning_percent == 7.0
    assert settings.readiness.resting_hr.critical_percent == 12.0

    assert settings.readiness.sleep_duration.warning_hours == 6.0
    assert settings.readiness.sleep_duration.critical_hours == 4.5

    assert settings.readiness.sleep_score.warning_value == 65.0
    assert settings.readiness.sleep_score.critical_value == 50.0

    assert settings.readiness.training_load.warning_balance == -10.0
    assert settings.readiness.training_load.critical_balance == -20.0

def test_threshold_settings_accept_custom_values(
    tmp_path: Path,
) -> None:
    config_path = (
        tmp_path
        / "thresholds.toml"
    )

    config_path.write_text(
    """
        [activity_matching]
        best_match_score = 82.0

        [readiness.baseline]
        window_days = 21
        minimum_samples = 10

        [readiness.score]
        high_min = 90.0
        good_min = 75.0
        moderate_min = 55.0
        low_min = 35.0
        single_critical_cap = 58.0
        multiple_critical_cap = 28.0

        [readiness.penalties]
        warning = 12.0
        critical = 30.0

        [readiness.hrv]
        warning_percent = -12.0
        critical_percent = -25.0

        [readiness.resting_hr]
        warning_percent = 8.0
        critical_percent = 15.0

        [readiness.sleep_duration]
        warning_percent = -18.0
        critical_percent = -35.0
        warning_hours = 6.5
        critical_hours = 5.0

        [readiness.sleep_score]
        warning_value = 68.0
        critical_value = 52.0

        [readiness.training_load]
        warning_balance = -12.0
        critical_balance = -24.0
        """.strip(),
            encoding="utf-8",
        )

    settings = load_threshold_settings(
        config_path,
    )

    assert (
        settings
        .activity_matching
        .best_match_score
        == 82.0
    )

    assert (
        settings
        .readiness
        .baseline
        .window_days
        == 21
    )

    assert (
        settings
        .readiness
        .baseline
        .minimum_samples
        == 10
    )


def test_threshold_settings_reject_invalid_match_score(
    tmp_path: Path,
) -> None:
    config_path = (
        tmp_path
        / "thresholds.toml"
    )

    config_path.write_text(
        """
[activity_matching]
best_match_score = 150.0

[readiness.baseline]
window_days = 14
minimum_samples = 7

[readiness.score]
high_min = 85.0
good_min = 70.0
moderate_min = 50.0
low_min = 30.0
single_critical_cap = 60.0
multiple_critical_cap = 29.0

[readiness.penalties]
warning = 10.0
critical = 25.0

[readiness.hrv]
warning_percent = -10.0
critical_percent = -20.0

[readiness.resting_hr]
warning_percent = 7.0
critical_percent = 12.0

[readiness.sleep_duration]
warning_percent = -15.0
critical_percent = -30.0
warning_hours = 6.0
critical_hours = 4.5

[readiness.sleep_score]
warning_value = 65.0
critical_value = 50.0

[readiness.training_load]
warning_balance = -10.0
critical_balance = -20.0
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(
        ThresholdConfigurationError,
    ):
        load_threshold_settings(
            config_path,
        )

def test_threshold_settings_reject_too_many_samples(
    tmp_path: Path,
) -> None:
    config_path = (
        tmp_path
        / "thresholds.toml"
    )

    config_path.write_text(
        """
[activity_matching]
best_match_score = 75.0

[readiness.baseline]
window_days = 7
minimum_samples = 10

[readiness.score]
high_min = 85.0
good_min = 70.0
moderate_min = 50.0
low_min = 30.0
single_critical_cap = 60.0
multiple_critical_cap = 29.0

[readiness.penalties]
warning = 10.0
critical = 25.0

[readiness.hrv]
warning_percent = -10.0
critical_percent = -20.0

[readiness.resting_hr]
warning_percent = 7.0
critical_percent = 12.0

[readiness.sleep_duration]
warning_percent = -15.0
critical_percent = -30.0
warning_hours = 6.0
critical_hours = 4.5

[readiness.sleep_score]
warning_value = 65.0
critical_value = 50.0

[readiness.training_load]
warning_balance = -10.0
critical_balance = -20.0
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(
        ThresholdConfigurationError,
    ):
        load_threshold_settings(
            config_path,
        )