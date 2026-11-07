"""Tests de configuration du moteur IA."""

import pytest

from opencoach.ai.config import (
    AIConfigurationError,
    AISettings,
    clear_ai_settings_cache,
    get_ai_settings,
)


@pytest.fixture(autouse=True)
def clear_cache():
    clear_ai_settings_cache()
    yield
    clear_ai_settings_cache()


def test_ai_is_disabled_by_default(monkeypatch):
    for key in (
        "OPENCOACH_AI_ENABLED",
        "OPENCOACH_AI_PROVIDER",
        "OPENCOACH_AI_BASE_URL",
        "OPENCOACH_AI_MODEL",
        "OPENCOACH_AI_CONNECT_TIMEOUT_SECONDS",
        "OPENCOACH_AI_READ_TIMEOUT_SECONDS",
        "OPENCOACH_AI_MAX_CONCURRENCY",
    ):
        monkeypatch.delenv(key, raising=False)

    settings = AISettings.from_environment()

    assert settings.enabled is False
    assert settings.provider == "ollama"
    assert settings.max_concurrency == 1


def test_reads_ai_environment(monkeypatch):
    monkeypatch.setenv("OPENCOACH_AI_ENABLED", "true")
    monkeypatch.setenv("OPENCOACH_AI_MODEL", "qwen3:8b")
    monkeypatch.setenv("OPENCOACH_AI_MAX_CONCURRENCY", "2")

    settings = AISettings.from_environment()

    assert settings.enabled is True
    assert settings.model == "qwen3:8b"
    assert settings.max_concurrency == 2


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("OPENCOACH_AI_ENABLED", "sometimes"),
        ("OPENCOACH_AI_PROVIDER", "openai"),
        ("OPENCOACH_AI_BASE_URL", "file:///tmp/model"),
        ("OPENCOACH_AI_MODEL", "../unsafe"),
        ("OPENCOACH_AI_CONNECT_TIMEOUT_SECONDS", "0"),
        ("OPENCOACH_AI_CONNECT_TIMEOUT_SECONDS", "nan"),
        ("OPENCOACH_AI_CONNECT_TIMEOUT_SECONDS", "inf"),
        ("OPENCOACH_AI_CONNECT_TIMEOUT_SECONDS", "-inf"),
        ("OPENCOACH_AI_READ_TIMEOUT_SECONDS", "-1"),
        ("OPENCOACH_AI_READ_TIMEOUT_SECONDS", "nan"),
        ("OPENCOACH_AI_READ_TIMEOUT_SECONDS", "inf"),
        ("OPENCOACH_AI_MAX_CONCURRENCY", "0"),
        ("OPENCOACH_AI_MAX_CONCURRENCY", "9"),
    ],
)
def test_rejects_invalid_configuration(monkeypatch, key, value):
    monkeypatch.setenv(key, value)

    with pytest.raises(AIConfigurationError):
        AISettings.from_environment()
