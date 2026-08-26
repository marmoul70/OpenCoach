from datetime import date

from opencoach.planning.sessions.intent import (
    SessionIntent,
    SessionIntentImportance,
)
from opencoach.planning.stimulus.training import (
    SpecificityLevel,
    SubstitutionPolicy,
    TrainingModality,
    TrainingStimulus,
)
from opencoach.planning.weekly.schedule_capacity import (
    DayScheduleCapacity,
)
from opencoach.planning.weekly.schedule_types import (
    Weekday,
)
from opencoach.planning.weekly.training_envelope_builder import (
    _apply_race_protection,
)


def test_pre_race_days_block_quality_and_strength() -> None:
    capacities = _apply_race_protection(
        week_start=date(
            2026,
            8,
            24,
        ),
        available_days=(
            Weekday.MONDAY,
            Weekday.WEDNESDAY,
            Weekday.THURSDAY,
            Weekday.FRIDAY,
            Weekday.SATURDAY,
        ),
        day_capacities=(),
        protection_dates=(
            date(2026, 8, 24),
            date(2026, 8, 25),
            date(2026, 8, 26),
            date(2026, 8, 27),
            date(2026, 8, 28),
            date(2026, 8, 29),
        ),
    )

    for capacity in capacities:
        assert (
            capacity.allows_load_category(
                __import__(
                    "opencoach.planning.stimulus.training",
                    fromlist=[
                        "StimulusLoadCategory"
                    ],
                ).StimulusLoadCategory.QUALITY
            )
            is False
        )

        assert (
            capacity.allows_load_category(
                __import__(
                    "opencoach.planning.stimulus.training",
                    fromlist=[
                        "StimulusLoadCategory"
                    ],
                ).StimulusLoadCategory.STRENGTH
            )
            is False
        )
