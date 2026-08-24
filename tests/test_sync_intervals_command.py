from datetime import (
    date,
    datetime,
    timezone,
)
from uuid import uuid4

import pytest

from opencoach.commands.sync_intervals import (
    main,
)
from opencoach.services import (
    IntervalsSyncResult,
)


class FakeCommandService:
    def __init__(
        self,
        result: IntervalsSyncResult,
    ) -> None:
        self.result = result
        self.calls = []

    def sync_incremental(
        self,
        athlete_profile_id,
        *,
        initial_days: int,
        lookback_days: int,
    ) -> IntervalsSyncResult:
        self.calls.append(
            (
                athlete_profile_id,
                initial_days,
                lookback_days,
            )
        )

        return self.result


def create_result() -> IntervalsSyncResult:
    return IntervalsSyncResult(
        synced_activities=3,
        synced_wellness_days=2,
        oldest=date(2026, 8, 20),
        newest=date(2026, 8, 24),
        synced_at=datetime(
            2026,
            8,
            24,
            16,
            30,
            tzinfo=timezone.utc,
        ),
    )


def test_command_runs_incremental_sync(
    capsys,
) -> None:
    profile_id = uuid4()

    service = FakeCommandService(
        create_result()
    )

    exit_code = main(
        argv=[],
        service=service,
        athlete_profile_id=profile_id,
    )

    assert exit_code == 0

    assert service.calls == [
        (
            profile_id,
            30,
            2,
        )
    ]

    output = capsys.readouterr().out

    assert "3 activité" in output
    assert "2 jour" in output


def test_command_accepts_sync_policy_options() -> None:
    profile_id = uuid4()

    service = FakeCommandService(
        create_result()
    )

    exit_code = main(
        argv=[
            "--initial-days",
            "60",
            "--lookback-days",
            "3",
        ],
        service=service,
        athlete_profile_id=profile_id,
    )

    assert exit_code == 0

    assert service.calls == [
        (
            profile_id,
            60,
            3,
        )
    ]


@pytest.mark.parametrize(
    "argv",
    [
        ["--initial-days", "0"],
        ["--lookback-days", "-1"],
    ],
)
def test_command_rejects_invalid_policy(
    argv,
) -> None:
    with pytest.raises(
        SystemExit,
    ):
        main(
            argv=argv,
            service=FakeCommandService(
                create_result()
            ),
            athlete_profile_id=uuid4(),
        )
