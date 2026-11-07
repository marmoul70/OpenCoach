"""Moteur IA local optionnel d'OpenCoach."""

from opencoach.ai.config import AISettings, get_ai_settings
from opencoach.ai.service import AIService, AIServiceDisabledError

__all__ = [
    "AIService",
    "AIServiceDisabledError",
    "AISettings",
    "get_ai_settings",
]
