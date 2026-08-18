from pydantic import BaseModel, Field


class DailyContextUpdate(BaseModel):
    """Données subjectives saisies par l'athlète."""

    fatigue_subjective: int = Field(
        ge=1,
        le=5,
    )

    pain_level: int = Field(
        ge=0,
        le=10,
    )

    illness_status: str = Field(
        pattern=r"^(none|mild|significant)$",
    )

    treatment_impact: str = Field(
        pattern=r"^(none|mild|significant)$",
    )

    motivation: int = Field(
        ge=1,
        le=5,
    )

    notes: str | None = Field(
        default=None,
        max_length=2000,
    )


class DailyContextResponse(BaseModel):
    """Contexte subjectif quotidien retourné par l'API."""

    date: str

    fatigue_subjective: int
    pain_level: int

    illness_status: str
    treatment_impact: str

    motivation: int

    notes: str | None
