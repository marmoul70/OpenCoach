"""Classification physiologique des intentions de séance."""

from __future__ import annotations

from opencoach.planning.sessions.intent import (
    SessionIntent,
)
from opencoach.planning.stimulus.families import (
    StimulusFamily,
    stimulus_family,
)


def session_intent_family(
    intent: SessionIntent,
) -> StimulusFamily:
    """Retourne la famille du stimulus principal d'une intention."""

    return stimulus_family(
        intent.primary_stimulus
    )
