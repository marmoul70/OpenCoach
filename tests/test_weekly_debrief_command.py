from __future__ import annotations

from datetime import date, datetime, timezone
from types import SimpleNamespace

from opencoach.commands.run_weekly_debrief import (
    main,
)


class FakeApplication:
    def __init__(
        self,
        *,
        completed: int = 0,
        already_completed: int = 0,
        waiting: int = 0,
        no_debrief: int = 0,
        failed: int = 0,
    ) -> None:
        self.batch = SimpleNamespace(
            completed=completed,
            already_completed=(
                already_completed
            ),
            waiting=waiting,
            no_debrief=no_debrief,
            failed=failed,
        )

        self.calls: list[dict] = []

    def execute(
        self,
        *,
        reference_date,
        now,
    ):
        self.calls.append(
            {
                "reference_date":
                    reference_date,
                "now":
                    now,
            }
        )

        return self.batch


def test_command_uses_execution_date_by_default(
    capsys,
) -> None:
    application = FakeApplication(
        completed=1,
        waiting=2,
    )

    execution_time = datetime(
        2026,
        8,
        30,
        20,
        30,
        tzinfo=timezone.utc,
    )

    result = main(
        [],
        application_service=application,
        now=execution_time,
    )

    assert result == 0

    assert application.calls == [
        {
            "reference_date":
                date(
                    2026,
                    8,
                    30,
                ),
            "now":
                execution_time,
        }
    ]

    output = (
        capsys
        .readouterr()
        .out
    )

    assert "Clôturés" in output
    assert "En attente" in output


def test_command_accepts_explicit_reference_date() -> None:
    application = FakeApplication()

    execution_time = datetime(
        2026,
        9,
        6,
        21,
        0,
        tzinfo=timezone.utc,
    )

    result = main(
        [
            "--reference-date",
            "2026-08-30",
        ],
        application_service=application,
        now=execution_time,
    )

    assert result == 0

    assert (
        application.calls[0]
        ["reference_date"]
        == date(
            2026,
            8,
            30,
        )
    )


def test_command_returns_failure_when_batch_failed(
    capsys,
) -> None:
    application = FakeApplication(
        completed=1,
        failed=2,
    )

    result = main(
        [],
        application_service=application,
        now=datetime(
            2026,
            8,
            30,
            22,
            0,
            tzinfo=timezone.utc,
        ),
    )

    assert result == 1

    output = (
        capsys
        .readouterr()
        .out
    )

    assert "2 échec(s)" in output


def test_command_rejects_invalid_reference_date() -> None:
    application = FakeApplication()

    try:
        main(
            [
                "--reference-date",
                "30-08-2026",
            ],
            application_service=(
                application
            ),
            now=datetime(
                2026,
                8,
                30,
                22,
                0,
                tzinfo=timezone.utc,
            ),
        )

    except SystemExit as exc:
        assert exc.code == 2

    else:
        raise AssertionError(
            "La date invalide aurait dû "
            "être rejetée."
        )

    assert application.calls == []
