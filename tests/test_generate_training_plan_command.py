from __future__ import annotations

import pytest

from opencoach.commands.generate_training_plan import build_parser


def test_manual_generation_requires_explicit_target() -> None:
    with pytest.raises(SystemExit) as exc_info:
        build_parser().parse_args([])

    assert exc_info.value.code == 2


def test_manual_generation_accepts_username_and_week_count() -> None:
    args = build_parser().parse_args(
        ["--username", "runner01", "--weeks", "3"]
    )

    assert args.username == "runner01"
    assert args.all_active is False
    assert args.weeks == 3


def test_manual_generation_can_target_all_active_profiles() -> None:
    args = build_parser().parse_args(["--all-active"])

    assert args.all_active is True
    assert args.username is None
    assert args.weeks == 2


def test_manual_generation_rejects_invalid_week_count() -> None:
    with pytest.raises(SystemExit) as exc_info:
        build_parser().parse_args(
            ["--username", "runner01", "--weeks", "0"]
        )

    assert exc_info.value.code == 2


def test_manual_generation_rejects_invalid_reference_date() -> None:
    with pytest.raises(SystemExit) as exc_info:
        build_parser().parse_args(
            [
                "--username",
                "runner01",
                "--reference-date",
                "22/11/2026",
            ]
        )

    assert exc_info.value.code == 2
