"""Allocation des durées de séances OpenCoach."""

from .allocator import (
    allocate_session_durations,
)
from .models import (
    AllocatedSessionDuration,
)

__all__ = [
    "AllocatedSessionDuration",
    "allocate_session_durations",
]
