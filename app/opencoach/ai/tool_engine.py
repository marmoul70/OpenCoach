"""Compatibilité historique vers le registre de capacités Coach.

Le moteur IA ne possède plus ni le registre ni l'exécuteur des capacités métier.
"""

from opencoach.coaching.capabilities.registry import (
    CoachCapability as AITool,
    CoachCapabilityRegistry as AIToolRegistry,
    CoachCapabilityResult as AIToolResult,
    CoachCapabilityResult,
    CoachCapability,
    CoachCapabilityRegistry,
)

ToolStatus = str
