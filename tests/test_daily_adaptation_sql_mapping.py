from uuid import uuid4

from opencoach.coaching.daily_adaptation import (
    AdaptationDecision,
)
from opencoach.database.models.daily_adaptation import (
    DailyAdaptationProposal,
)
from opencoach.database.repositories.sql_daily_adaptation import (
    SqlDailyAdaptationRepository,
)


def test_daily_adaptation_sql_model_maps_to_domain() -> None:
    proposal_id = uuid4()
    checkin_id = uuid4()

    model = DailyAdaptationProposal(
        id=proposal_id,
        athlete_profile_id=uuid4(),
        checkin_id=checkin_id,
        reason="Douleur modérée.",
        recommendation="Adapter la séance ?",
        decision="declined",
    )

    result = (
        SqlDailyAdaptationRepository
        ._to_domain(model)
    )

    assert result.id == proposal_id
    assert result.checkin_id == checkin_id

    assert (
        result.decision
        is AdaptationDecision.DECLINED
    )

    assert not result.adaptation_authorized
