"""Tests de résolution dynamique de l'objectif du coach."""

from datetime import date
from uuid import uuid4

from opencoach.coaching.replanning import (
    CoachingGoalMode,
    CoachingGoalResolution,
    CoachingGoalResolver,
)
from opencoach.models import Race


def create_race(
    *,
    race_date: date,
    priority: str = "primary",
    status: str = "planned",
    name: str = "Course",
) -> Race:
    return Race(
        id=uuid4(),
        date=race_date,
        name=name,
        location="Test",
        race_type="trail",
        priority=priority,
        distance_km=50.0,
        elevation_gain_m=2500.0,
        status=status,
    )


class FakeRaceRepository:
    def __init__(
        self,
        races: list[Race],
    ) -> None:
        self.races = races
        self.calls = []

    def list_upcoming_races(
        self,
        athlete_profile_id,
        from_date: date,
    ) -> list[Race]:
        self.calls.append(
            (
                athlete_profile_id,
                from_date,
            )
        )

        return [
            race
            for race in self.races
            if (
                race.date >= from_date
                and race.status == "planned"
            )
        ]


def test_resolver_selects_next_planned_primary() -> None:
    planning_date = date(
        2026,
        8,
        24,
    )

    first = create_race(
        race_date=date(
            2026,
            9,
            15,
        ),
        name="Objectif proche",
    )

    second = create_race(
        race_date=date(
            2027,
            5,
            16,
        ),
        name="Objectif mai",
    )

    repository = FakeRaceRepository(
        [
            first,
            second,
        ]
    )

    resolver = CoachingGoalResolver(
        race_repository=repository,
    )

    result = resolver.resolve(
        athlete_profile_id=uuid4(),
        planning_date=planning_date,
    )

    assert result.mode is CoachingGoalMode.TARGET_RACE
    assert result.target_race is first
    assert result.target_race.date == date(
        2026,
        9,
        15,
    )


def test_withdrawn_primary_is_ignored_and_next_primary_is_selected() -> None:
    planning_date = date(
        2026,
        8,
        24,
    )

    withdrawn = create_race(
        race_date=date(
            2026,
            9,
            15,
        ),
        status="not_participated",
        name="Course annulée",
    )

    next_goal = create_race(
        race_date=date(
            2027,
            5,
            16,
        ),
        status="planned",
        name="Objectif mai 2027",
    )

    resolver = CoachingGoalResolver(
        race_repository=FakeRaceRepository(
            [
                withdrawn,
                next_goal,
            ]
        ),
    )

    result = resolver.resolve(
        athlete_profile_id=uuid4(),
        planning_date=planning_date,
    )

    assert result.mode is CoachingGoalMode.TARGET_RACE
    assert result.target_race is next_goal
    assert result.target_race.name == "Objectif mai 2027"


def test_training_race_does_not_become_primary_goal() -> None:
    planning_date = date(
        2026,
        8,
        24,
    )

    training_race = create_race(
        race_date=date(
            2026,
            10,
            1,
        ),
        priority="training",
    )

    primary = create_race(
        race_date=date(
            2027,
            5,
            16,
        ),
        priority="primary",
    )

    resolver = CoachingGoalResolver(
        race_repository=FakeRaceRepository(
            [
                training_race,
                primary,
            ]
        ),
    )

    result = resolver.resolve(
        athlete_profile_id=uuid4(),
        planning_date=planning_date,
    )

    assert result.mode is CoachingGoalMode.TARGET_RACE
    assert result.target_race is primary


def test_no_primary_race_switches_to_maintenance() -> None:
    resolver = CoachingGoalResolver(
        race_repository=FakeRaceRepository(
            []
        ),
    )

    result = resolver.resolve(
        athlete_profile_id=uuid4(),
        planning_date=date(
            2026,
            8,
            24,
        ),
    )

    assert (
        result.mode
        is CoachingGoalMode.MAINTENANCE
    )

    assert result.target_race is None


def test_only_training_races_keep_maintenance_mode() -> None:
    resolver = CoachingGoalResolver(
        race_repository=FakeRaceRepository(
            [
                create_race(
                    race_date=date(
                        2026,
                        10,
                        1,
                    ),
                    priority="training",
                )
            ]
        ),
    )

    result = resolver.resolve(
        athlete_profile_id=uuid4(),
        planning_date=date(
            2026,
            8,
            24,
        ),
    )

    assert (
        result.mode
        is CoachingGoalMode.MAINTENANCE
    )

    assert result.target_race is None


def test_resolution_exposes_weeks_until_target() -> None:
    planning_date = date(
        2026,
        8,
        24,
    )

    target = create_race(
        race_date=date(
            2026,
            9,
            21,
        ),
    )

    resolver = CoachingGoalResolver(
        race_repository=FakeRaceRepository(
            [target]
        ),
    )

    result = resolver.resolve(
        athlete_profile_id=uuid4(),
        planning_date=planning_date,
    )

    assert result.days_until_target == 28
    assert result.weeks_until_target == 4.0


def test_maintenance_has_no_target_horizon() -> None:
    result = CoachingGoalResolution(
        mode=CoachingGoalMode.MAINTENANCE,
        target_race=None,
        planning_date=date(
            2026,
            8,
            24,
        ),
    )

    assert result.days_until_target is None
    assert result.weeks_until_target is None
