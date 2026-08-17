import pytest

from opencoach.config import IntervalsSettings


def test_intervals_settings_are_loaded_from_environment(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "INTERVALS_API_KEY",
        "test-api-key",
    )
    monkeypatch.setenv(
        "INTERVALS_ATHLETE_ID",
        "i123456",
    )

    settings = IntervalsSettings.from_env()

    assert settings.api_key == "test-api-key"
    assert settings.athlete_id == "i123456"


def test_intervals_api_key_is_required(
    monkeypatch,
) -> None:
    monkeypatch.delenv(
        "INTERVALS_API_KEY",
        raising=False,
    )
    monkeypatch.setenv(
        "INTERVALS_ATHLETE_ID",
        "i123456",
    )

    with pytest.raises(
        RuntimeError,
        match="INTERVALS_API_KEY",
    ):
        IntervalsSettings.from_env()


def test_intervals_athlete_id_is_required(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "INTERVALS_API_KEY",
        "test-api-key",
    )
    monkeypatch.delenv(
        "INTERVALS_ATHLETE_ID",
        raising=False,
    )

    with pytest.raises(
        RuntimeError,
        match="INTERVALS_ATHLETE_ID",
    ):
        IntervalsSettings.from_env()


def test_intervals_settings_trim_environment_values(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "INTERVALS_API_KEY",
        "  test-api-key  ",
    )
    monkeypatch.setenv(
        "INTERVALS_ATHLETE_ID",
        "  i123456  ",
    )

    settings = IntervalsSettings.from_env()

    assert settings.api_key == "test-api-key"
    assert settings.athlete_id == "i123456"