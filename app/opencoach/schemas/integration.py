from pydantic import BaseModel, Field
from datetime import datetime

class IntervalsConnectionUpdate(BaseModel):
    """Données saisies pour configurer Intervals.icu."""

    athlete_id: str = Field(
        min_length=1,
        max_length=255,
    )

    api_key: str | None = Field(
        default=None,
        max_length=1000,
    )

    web_cookie: str | None = Field(
        default=None,
        max_length=4000,
    )

    enabled: bool = True


class IntervalsConnectionResponse(BaseModel):
    """Configuration Intervals.icu exposable au frontend."""

    provider: str = "intervals"
    configured: bool
    enabled: bool
    athlete_id: str | None
    api_key_configured: bool
    web_cookie_configured: bool = False
    last_synced_at: datetime | None = None


class IntervalsConnectionTest(BaseModel):
    """Credentials temporaires utilisés pour tester Intervals.icu."""

    athlete_id: str = Field(
        min_length=1,
        max_length=255,
    )

    api_key: str = Field(
        min_length=1,
        max_length=1000,
    )

    web_cookie: str | None = Field(
        default=None,
        max_length=4000,
    )


class IntervalsConnectionTestResponse(BaseModel):
    provider: str = "intervals"
    connected: bool
    athlete_id: str


class IntervalsWebCookieTest(BaseModel):
    """Cookie temporaire utilisé pour tester la synchronisation partenaire."""

    web_cookie: str | None = Field(
        default=None,
        max_length=4000,
    )
