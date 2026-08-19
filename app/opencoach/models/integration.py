from dataclasses import dataclass
from datetime import datetime


@dataclass
class IntegrationConnection:
    """Configuration d'une intégration externe OpenCoach."""

    provider: str
    enabled: bool = True

    athlete_id: str | None = None

    secret_configured: bool = False

    last_synced_at: datetime | None = None