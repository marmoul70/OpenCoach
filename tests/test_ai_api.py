"""Tests de l'API de diagnostic IA."""

from fastapi.testclient import TestClient

from opencoach.ai.config import AISettings, get_ai_settings
from opencoach.api.app import create_app
from opencoach.authentication.auth import COOKIE_NAME


def _client(settings: AISettings) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_ai_settings] = lambda: settings
    client = TestClient(app)
    client.cookies.set(COOKIE_NAME, "test-session-token")
    return client


def test_ai_status_reports_disabled_by_default_without_provider_call() -> None:
    client = _client(AISettings())

    response = client.get("/api/ai/status")

    assert response.status_code == 200
    assert response.json() == {
        "enabled": False,
        "provider": "ollama",
        "model": "phi4-mini:latest",
        "provider_check": "not_checked",
    }


def test_ai_status_reports_configuration_without_exposing_provider_url() -> None:
    settings = AISettings(
        enabled=True,
        provider="ollama",
        base_url="http://127.0.0.1:11434",
        model="qwen3:8b",
    )
    client = _client(settings)

    response = client.get("/api/ai/status")

    assert response.status_code == 200
    assert response.json() == {
        "enabled": True,
        "provider": "ollama",
        "model": "qwen3:8b",
        "provider_check": "not_checked",
    }
    assert "base_url" not in response.json()
