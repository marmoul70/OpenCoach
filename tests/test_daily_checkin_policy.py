from datetime import date

import pytest

from opencoach.coaching.daily_checkin import (
    AthleteDailyCheckIn,
    BodySide,
    PainArea,
    PainLocation,
)
from opencoach.coaching.daily_checkin_policy import (
    CheckInCoachAction,
    assess_daily_checkin,
)


TODAY = date(
    2026,
    8,
    26,
)


def checkin(
    *,
    energy=5,
    pain=5,
    illness=False,
    unavailable=False,
    locations=(),
):
    return AthleteDailyCheckIn(
        date=TODAY,
        energy_rating=energy,
        pain_wellness_rating=pain,
        illness=illness,
        unavailable=unavailable,
        pain_locations=locations,
    )


def test_rating_must_be_between_one_and_five() -> None:
    with pytest.raises(ValueError):
        checkin(
            energy=0,
        )

    with pytest.raises(ValueError):
        checkin(
            pain=6,
        )


def test_five_five_requires_no_action() -> None:
    result = assess_daily_checkin(
        checkin()
    )

    assert (
        result.action
        is CheckInCoachAction.NONE
    )

    assert not (
        result.adaptation_requires_athlete_decision
    )

    assert not (
        result.increased_debrief_attention
    )


def test_four_hearts_only_requires_monitoring() -> None:
    result = assess_daily_checkin(
        checkin(
            pain=4,
        )
    )

    assert (
        result.action
        is CheckInCoachAction.MONITOR
    )

    assert not (
        result.adaptation_requires_athlete_decision
    )

    assert (
        result.increased_debrief_attention
    )


def test_three_hearts_offers_adaptation() -> None:
    result = assess_daily_checkin(
        checkin(
            pain=3,
            locations=(
                PainLocation(
                    area=PainArea.LOWER_BACK,
                    side=BodySide.CENTER,
                ),
            ),
        )
    )

    assert (
        result.action
        is CheckInCoachAction.OFFER_ADAPTATION
    )

    assert (
        result.adaptation_requires_athlete_decision
    )

    assert (
        result.increased_debrief_attention
    )


def test_two_hearts_strongly_recommends_adaptation() -> None:
    result = assess_daily_checkin(
        checkin(
            pain=2,
        )
    )

    assert (
        result.action
        is CheckInCoachAction
        .STRONGLY_RECOMMEND_ADAPTATION
    )

    assert (
        result.adaptation_requires_athlete_decision
    )


def test_three_stars_offers_adaptation() -> None:
    result = assess_daily_checkin(
        checkin(
            energy=3,
        )
    )

    assert (
        result.action
        is CheckInCoachAction.OFFER_ADAPTATION
    )


def test_low_energy_strongly_recommends_adaptation() -> None:
    result = assess_daily_checkin(
        checkin(
            energy=1,
        )
    )

    assert (
        result.action
        is CheckInCoachAction
        .STRONGLY_RECOMMEND_ADAPTATION
    )


def test_illness_strongly_recommends_adaptation() -> None:
    result = assess_daily_checkin(
        checkin(
            illness=True,
        )
    )

    assert (
        result.action
        is CheckInCoachAction
        .STRONGLY_RECOMMEND_ADAPTATION
    )

    assert result.illness_reported


def test_unavailable_is_not_interpreted_as_fatigue() -> None:
    result = assess_daily_checkin(
        checkin(
            unavailable=True,
        )
    )

    assert result.unavailable_reported

    assert (
        result.action
        is CheckInCoachAction
        .STRONGLY_RECOMMEND_ADAPTATION
    )

    assert not result.illness_reported


def test_pain_location_is_preserved_for_coach_reasoning() -> None:
    result = assess_daily_checkin(
        checkin(
            pain=3,
            locations=(
                PainLocation(
                    area=PainArea.ACHILLES,
                    side=BodySide.LEFT,
                ),
            ),
        )
    )

    assert any(
        "achilles:left"
        in reason
        for reason in result.reasons
    )


def test_multiple_signals_keep_most_cautious_action() -> None:
    result = assess_daily_checkin(
        checkin(
            energy=3,
            pain=2,
        )
    )

    assert (
        result.action
        is CheckInCoachAction
        .STRONGLY_RECOMMEND_ADAPTATION
    )


def test_five_hearts_cannot_have_pain_location() -> None:
    with pytest.raises(ValueError):
        checkin(
            pain=5,
            locations=(
                PainLocation(
                    area=PainArea.KNEE,
                    side=BodySide.LEFT,
                ),
            ),
        )
