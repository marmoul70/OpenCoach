from datetime import date
from uuid import uuid4

from opencoach.coaching.daily_checkin import (
    BodySide,
    PainArea,
)
from opencoach.database.models.daily_checkin import (
    DailyCheckIn,
)
from opencoach.database.repositories.sql_daily_checkin import (
    SqlDailyCheckInRepository,
)


def test_daily_checkin_sql_model_maps_to_domain() -> None:
    checkin_id = uuid4()

    model = DailyCheckIn(
        id=checkin_id,
        athlete_profile_id=uuid4(),
        date=date(
            2026,
            8,
            26,
        ),
        energy_rating=3,
        pain_wellness_rating=3,
        illness=False,
        unavailable=False,
        pain_locations=[
            {
                "area": "lower_back",
                "side": "center",
            }
        ],
        note="Dos sensible.",
    )

    result = (
        SqlDailyCheckInRepository
        ._to_domain(model)
    )

    assert result.id == checkin_id
    assert result.energy_rating == 3
    assert result.pain_wellness_rating == 3

    assert (
        result.pain_locations[0].area
        is PainArea.LOWER_BACK
    )

    assert (
        result.pain_locations[0].side
        is BodySide.CENTER
    )
