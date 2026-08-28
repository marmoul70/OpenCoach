from datetime import datetime
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from opencoach.database.base import Base
from opencoach.database.models import (
    Activity as ActivityModel,
)
from opencoach.database.repositories import (
    SqlActivityDetailRepository,
)
from opencoach.models import (
    ActivityDetail,
    ActivityInterval,
    ActivityStream,
    ActivityStreams,
)


def create_detail() -> ActivityDetail:
    return ActivityDetail(
        provider_activity_id="i176833684",
        intervals=(
            ActivityInterval(
                provider_interval_id="5935911",
                interval_type="WORK",
                label=None,
                start_index=0,
                end_index=364,
                start_time_seconds=0,
                end_time_seconds=364,
                distance_m=999.0,
                moving_time_seconds=364,
                elapsed_time_seconds=364,
                average_speed_mps=2.7445,
                average_heart_rate=114.0,
                max_heart_rate=128.0,
                average_cadence=88.1,
                elevation_gain_m=5.2,
            ),
        ),
        streams=ActivityStreams(
            time=ActivityStream(
                stream_type="time",
                data=(0, 1, 2),
            ),
            heartrate=ActivityStream(
                stream_type="heartrate",
                data=(79, 80, 81),
            ),
            distance=ActivityStream(
                stream_type="distance",
                data=(0.0, None, 9.0),
            ),
        ),
        interval_summary=(
            "6x 61s 154bpm",
        ),
        provider_lap_count=21,
    )


def create_database():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:"
    )

    Base.metadata.create_all(engine)

    return engine


def insert_activity(
    session: Session,
    athlete_profile_id,
):
    activity = ActivityModel(
        athlete_profile_id=athlete_profile_id,
        provider="intervals",
        provider_activity_id="i176833684",
        name="Morning Course à pied",
        sport_type="Run",
        start_at=datetime(
            2026,
            8,
            1,
            8,
            17,
            40,
        ),
    )

    session.add(activity)
    session.commit()
    session.refresh(activity)

    return activity


def test_repository_round_trip_detail() -> None:
    engine = create_database()

    athlete_profile_id = uuid4()

    with Session(engine) as session:
        activity = insert_activity(
            session,
            athlete_profile_id,
        )

        repository = SqlActivityDetailRepository(
            session
        )

        repository.save_activity_detail(
            athlete_profile_id,
            create_detail(),
        )

        loaded = repository.get_activity_detail(
            athlete_profile_id,
            activity.id,
        )

        assert loaded is not None

        assert (
            loaded.provider_activity_id
            == "i176833684"
        )

        assert loaded.provider_lap_count == 21

        assert loaded.interval_summary == (
            "6x 61s 154bpm",
        )

        assert len(loaded.intervals) == 1

        assert (
            loaded.intervals[0].distance_m
            == 999.0
        )

        assert (
            loaded.streams.time is not None
        )

        assert (
            loaded.streams.heartrate is not None
        )

        assert (
            loaded.streams.distance is not None
        )

        assert (
            loaded.streams.distance.data
            == (
                0.0,
                None,
                9.0,
            )
        )


def test_repository_replaces_previous_detail() -> None:
    engine = create_database()

    athlete_profile_id = uuid4()

    with Session(engine) as session:
        activity = insert_activity(
            session,
            athlete_profile_id,
        )

        repository = SqlActivityDetailRepository(
            session
        )

        repository.save_activity_detail(
            athlete_profile_id,
            create_detail(),
        )

        replacement = ActivityDetail(
            provider_activity_id="i176833684",
            intervals=(),
            streams=ActivityStreams(
                time=ActivityStream(
                    stream_type="time",
                    data=(0, 1),
                ),
            ),
            interval_summary=(),
            provider_lap_count=0,
        )

        repository.save_activity_detail(
            athlete_profile_id,
            replacement,
        )

        loaded = repository.get_activity_detail(
            athlete_profile_id,
            activity.id,
        )

        assert loaded is not None
        assert loaded.intervals == ()
        assert loaded.provider_lap_count == 0

        assert (
            loaded.streams.available_types
            == ("time",)
        )


def test_repository_is_scoped_to_athlete() -> None:
    engine = create_database()

    owner_id = uuid4()
    other_id = uuid4()

    with Session(engine) as session:
        activity = insert_activity(
            session,
            owner_id,
        )

        repository = SqlActivityDetailRepository(
            session
        )

        repository.save_activity_detail(
            owner_id,
            create_detail(),
        )

        assert (
            repository.get_activity_detail(
                other_id,
                activity.id,
            )
            is None
        )
