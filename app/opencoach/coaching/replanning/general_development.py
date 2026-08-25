"""Façade de compatibilité du développement général.

L'implémentation appartient au domaine planning/trajectory.
Ce module conserve l'API publique historique du package replanning.
"""

from opencoach.planning.trajectory.general_development import (
    GeneralDevelopmentPhaseAllocation,
    GeneralDevelopmentPolicy,
    allocate_general_development_phases,
    build_general_development_trajectory,
)


__all__ = [
    "GeneralDevelopmentPhaseAllocation",
    "GeneralDevelopmentPolicy",
    "allocate_general_development_phases",
    "build_general_development_trajectory",
]
