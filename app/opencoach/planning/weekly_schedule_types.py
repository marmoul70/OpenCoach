"""Types transversaux de la planification hebdomadaire OpenCoach.

Ce module contient les concepts génériques partagés par les différents
composants de scheduling.

Ils ne décrivent ni un stimulus, ni une intention de séance, ni une
séance concrète.
"""

from __future__ import annotations

from enum import StrEnum


class Weekday(StrEnum):
    """Jour de la semaine utilisé par la planification."""

    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class FatigueBudget(StrEnum):
    """Fatigue acceptable générée par un créneau hebdomadaire."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
