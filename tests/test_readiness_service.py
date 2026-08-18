from datetime import date, timedelta
from uuid import UUID, uuid4

import pytest

from opencoach.config import (
    load_threshold_settings,
)
from opencoach.database.repositories.wellness import (
    WellnessRepository,
)
from opencoach.models import WellnessDay
from opencoach.readiness import (
    ReadinessDataUnavailableError,
    ReadinessService,
)


TARGET_DATE = date(
    2026,
    8,
    18,
)


class FakeWellnessRepository(
    WellnessRepository
):
    def __init__(
        self,
        *,
        current: WellnessDay | None,
        history: list[WellnessDay],
    ) -> None:
        self.current = current
        self.history = history

        self.get_by_date_calls = []
        self.list_range_calls = []

    def save_wellness_day(
        self,
        athlete_profile_id: UUID,
        wellness: WellnessDay,
    ) -> None:
        raise NotImplementedError

    def get_latest(
        self,
        athlete_profile_id: UUID,
    ) -> WellnessDay | None:
        return self.current

    def get_by_date(
        self,
        athlete_profile_id: UUID,
        wellness_date: date,
        *,
        provider: str | None = None,
    ) -> WellnessDay | None:
        self.get_by_date_calls.append(
            (
                athlete_profile_id,
                wellness_date,
                provider,
            )
        )

        if self.current is None:
            return None

        if self.current.date != wellness_date:
            return None

        if (
            provider is not None
            and self.current.provider != provider
        ):
            return None

        return self.current

    def list_range(
        self,
        athlete_profile_id: UUID,
        start_date: date,
        end_date: date,
        *,
        provider: str | None = None,
    ) -> list[WellnessDay]:
        self.list_range_calls.append(
            (
                athlete_profile_id,
                start_date,
                end_date,
                provider,
            )
        )

        return [
            wellness
            for wellness in self.history
            if (
                start_date
                <= wellness.date
                <= end_date
                and (
                    provider is None
                    or wellness.provider
                    == provider
                )
            )
        ]


def create_current_day() -> WellnessDay:
    return WellnessDay(
        provider="intervals",
        date=TARGET_DATE,
        fitness_ctl=40.0,
        fatigue_atl=35.0,
        hrv=50.0,
        resting_hr=46,
        sleep_seconds=27000,
        sleep_score=80.0,
    )


def create_history(
    *,
    days: int = 14,
) -> list[WellnessDay]:
    return [
        WellnessDay(
            provider="intervals",
            date=(
                TARGET_DATE
                - timedelta(
                    days=day,
                )
            ),
            fitness_ctl=40.0,
            fatigue_atl=35.0,
            hrv=50.0,
            resting_hr=46,
            sleep_seconds=27000,
            sleep_score=80.0,
        )
        for day in range(
            1,
            days + 1,
        )
    ]


def create_service(
    repository: WellnessRepository,
) -> ReadinessService:
    return ReadinessService(
        repository,
        thresholds=load_threshold_settings(),
        provider="intervals",
    )


def test_readiness_service_calculates_assessment() -> None:
    repository = FakeWellnessRepository(
        current=create_current_day(),
        history=create_history(),
    )

    service = create_service(
        repository
    )

    profile_id = uuid4()

    result = service.calculate(
        profile_id,
        TARGET_DATE,
    )

    assert result.date == TARGET_DATE
    assert result.provider == "intervals"

    assert result.current.date == TARGET_DATE

    assert result.baseline.hrv.median == 50.0
    assert result.baseline.hrv.sample_count == 14
    assert result.baseline.hrv.reliable is True

    assert (
        result.comparison.hrv.percent_delta
        == 0.0
    )

    assert result.readiness.score == 100.0
    assert result.readiness.level == "high"


def test_readiness_service_uses_configured_history_window() -> None:
    repository = FakeWellnessRepository(
        current=create_current_day(),
        history=create_history(),
    )

    service = create_service(
        repository
    )

    profile_id = uuid4()

    service.calculate(
        profile_id,
        TARGET_DATE,
    )

    assert repository.list_range_calls == [
        (
            profile_id,
            date(2026, 8, 4),
            date(2026, 8, 17),
            "intervals",
        )
    ]


def test_readiness_service_excludes_current_day_from_baseline() -> None:
    history = create_history()

    history.append(
        WellnessDay(
            provider="intervals",
            date=TARGET_DATE,
            hrv=999.0,
            resting_hr=150,
            sleep_seconds=1000,
            sleep_score=1.0,
        )
    )

    repository = FakeWellnessRepository(
        current=create_current_day(),
        history=history,
    )

    service = create_service(
        repository
    )

    result = service.calculate(
        uuid4(),
        TARGET_DATE,
    )

    assert result.baseline.hrv.median == 50.0
    assert result.baseline.resting_hr.median == 46.0
    assert result.baseline.sleep_seconds.median == 27000.0
    assert result.baseline.sleep_score.median == 80.0


def test_readiness_service_filters_provider() -> None:
    history = create_history()

    history.append(
        WellnessDay(
            provider="suunto",
            date=date(
                2026,
                8,
                10,
            ),
            hrv=200.0,
            resting_hr=100,
            sleep_seconds=5000,
            sleep_score=10.0,
        )
    )

    repository = FakeWellnessRepository(
        current=create_current_day(),
        history=history,
    )

    service = create_service(
        repository
    )

    result = service.calculate(
        uuid4(),
        TARGET_DATE,
    )

    assert result.provider == "intervals"
    assert result.baseline.hrv.median == 50.0


def test_readiness_service_raises_when_current_day_is_missing() -> None:
    repository = FakeWellnessRepository(
        current=None,
        history=create_history(),
    )

    service = create_service(
        repository
    )

    with pytest.raises(
        ReadinessDataUnavailableError,
        match="Aucune donnée Wellness disponible",
    ):
        service.calculate(
            uuid4(),
            TARGET_DATE,
        )


def test_readiness_service_handles_insufficient_baseline() -> None:
    repository = FakeWellnessRepository(
        current=create_current_day(),
        history=create_history(
            days=3,
        ),
    )

    service = create_service(
        repository
    )

    result = service.calculate(
        uuid4(),
        TARGET_DATE,
    )

    assert result.baseline.hrv.sample_count == 3
    assert result.baseline.hrv.reliable is False

    hrv_signal = next(
        signal
        for signal in result.readiness.signals
        if signal.metric == "hrv"
    )

    assert hrv_signal.level == "unavailable"


def test_readiness_service_detects_degraded_recovery() -> None:
    current = create_current_day()

    current.hrv = 35.0
    current.resting_hr = 55
    current.sleep_seconds = 4 * 3600
    current.sleep_score = 40.0

    repository = FakeWellnessRepository(
        current=current,
        history=create_history(),
    )

    service = create_service(
        repository
    )

    result = service.calculate(
        uuid4(),
        TARGET_DATE,
    )

    assert result.readiness.critical_count == 4
    assert result.readiness.score == 0.0
    assert result.readiness.level == "very_low"

    assert (
        "prefer_recovery_or_rest"
        in result.readiness.training_constraints
    )
