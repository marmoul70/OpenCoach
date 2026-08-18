from pydantic import BaseModel, Field


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

    enabled: bool = True


class IntervalsConnectionResponse(BaseModel):
    """Configuration Intervals.icu exposable au frontend."""

    provider: str = "intervals"
    configured: bool
    enabled: bool
    athlete_id: str | None
    api_key_configured: bool


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


class IntervalsConnectionTestResponse(BaseModel):
    provider: str = "intervals"
    connected: bool
    athlete_id: str
