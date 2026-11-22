"""Vérifie que le runtime OpenCoach ne monte plus de coach IA."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_backend_does_not_register_an_ai_router():
    source = (ROOT / "app" / "opencoach" / "api" / "app.py").read_text(
        encoding="utf-8"
    )

    assert "opencoach.api.ai" not in source
    assert "ai_router" not in source


def test_frontend_does_not_mount_the_ai_chat():
    source = (ROOT / "frontend" / "src" / "App.tsx").read_text(
        encoding="utf-8"
    )

    assert "CoachAIChat" not in source
