from __future__ import annotations

import subprocess
from dataclasses import dataclass

from fastapi import APIRouter


router = APIRouter(
    prefix="/api/system",
    tags=["system"],
)


@dataclass(frozen=True)
class UnitProperties:
    values: dict[str, str]

    def get(
        self,
        key: str,
        default: str = "",
    ) -> str:
        return self.values.get(
            key,
            default,
        )


@router.get(
    "/tasks",
)
def get_automated_tasks() -> dict[str, object]:
    """
    Retourne les timers systemd appartenant à OpenCoach.

    Cette route est strictement en lecture seule.
    Seules les unités `opencoach-*.timer` sont exposées.
    """

    timer_names = _list_opencoach_timers()

    tasks = [
        _build_task(
            timer_name
        )
        for timer_name in timer_names
    ]

    return {
        "tasks": tasks,
        "count": len(tasks),
    }


def _list_opencoach_timers() -> list[str]:
    output = _run_systemctl(
        "list-unit-files",
        "--type=timer",
        "--no-legend",
        "--no-pager",
        "--plain",
    )

    timers: list[str] = []

    for line in output.splitlines():
        columns = line.split()

        if not columns:
            continue

        unit = columns[0]

        if (
            unit.startswith(
                "opencoach-"
            )
            and unit.endswith(
                ".timer"
            )
        ):
            timers.append(
                unit
            )

    return sorted(
        timers
    )


def _build_task(
    timer_name: str,
) -> dict[str, object]:
    timer = _show_unit(
        timer_name,
        (
            "Id",
            "Description",
            "ActiveState",
            "SubState",
            "UnitFileState",
            "NextElapseUSecRealtime",
            "LastTriggerUSec",
            "Triggers",
        ),
    )

    service_name = (
        timer.get(
            "Triggers"
        )
        or timer_name.removesuffix(
            ".timer"
        )
        + ".service"
    )

    service = _show_unit(
        service_name,
        (
            "Id",
            "Description",
            "ActiveState",
            "SubState",
            "Result",
            "ExecMainCode",
            "ExecMainStatus",
        ),
        tolerate_missing=True,
    )

    timer_active = (
        timer.get(
            "ActiveState"
        )
        == "active"
    )

    unit_file_state = timer.get(
        "UnitFileState"
    )

    enabled = (
        unit_file_state
        in {
            "enabled",
            "enabled-runtime",
            "static",
        }
    )

    result = (
        service.get(
            "Result"
        )
        or None
    )

    last_run = _normalize_timestamp(
        timer.get(
            "LastTriggerUSec"
        )
    )

    next_run = _normalize_timestamp(
        timer.get(
            "NextElapseUSecRealtime"
        )
    )

    status = _calculate_status(
        active=timer_active,
        enabled=enabled,
        result=result,
        last_run=last_run,
    )

    return {
        "unit": timer_name,
        "service": service_name,
        "label": _task_label(
            timer_name,
            timer.get(
                "Description"
            ),
        ),
        "description": (
            timer.get(
                "Description"
            )
            or None
        ),
        "active": timer_active,
        "enabled": enabled,
        "unit_file_state":
            unit_file_state
            or None,
        "status": status,
        "last_result": result,
        "last_run": last_run,
        "next_run": next_run,
        "service_active_state": (
            service.get(
                "ActiveState"
            )
            or None
        ),
        "service_sub_state": (
            service.get(
                "SubState"
            )
            or None
        ),
        "exec_status": _optional_int(
            service.get(
                "ExecMainStatus"
            )
        ),
    }


def _calculate_status(
    *,
    active: bool,
    enabled: bool,
    result: str | None,
    last_run: str | None,
) -> str:
    if (
        result
        and result
        not in {
            "success",
        }
    ):
        return "error"

    if (
        not active
        or not enabled
    ):
        return "inactive"

    if last_run is None:
        return "pending"

    return "ok"


def _task_label(
    unit: str,
    description: str,
) -> str:
    labels = {
        "opencoach-intervals-sync.timer":
            "Synchronisation Intervals.icu",

        "opencoach-backup.timer":
            "Sauvegarde OpenCoach",
    }

    if unit in labels:
        return labels[
            unit
        ]

    if description:
        normalized = description.strip()

        if normalized:
            return normalized

    value = (
        unit
        .removeprefix(
            "opencoach-"
        )
        .removesuffix(
            ".timer"
        )
        .replace(
            "-",
            " ",
        )
    )

    return value.capitalize()


def _show_unit(
    unit: str,
    properties: tuple[str, ...],
    *,
    tolerate_missing: bool = False,
) -> UnitProperties:
    arguments = [
        "show",
        unit,
        "--no-pager",
    ]

    for property_name in properties:
        arguments.extend(
            [
                "--property",
                property_name,
            ]
        )

    try:
        output = _run_systemctl(
            *arguments
        )
    except RuntimeError:
        if tolerate_missing:
            return UnitProperties(
                {}
            )

        raise

    values: dict[str, str] = {}

    for line in output.splitlines():
        key, separator, value = (
            line.partition(
                "="
            )
        )

        if separator:
            values[
                key
            ] = value

    return UnitProperties(
        values
    )


def _run_systemctl(
    *arguments: str,
) -> str:
    try:
        result = subprocess.run(
            [
                "systemctl",
                *arguments,
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (
        OSError,
        subprocess.SubprocessError,
    ) as exc:
        raise RuntimeError(
            "Impossible d'interroger systemd."
        ) from exc

    return result.stdout


def _normalize_timestamp(
    value: str,
) -> str | None:
    normalized = value.strip()

    if (
        not normalized
        or normalized
        in {
            "n/a",
            "-",
        }
    ):
        return None

    return normalized


def _optional_int(
    value: str,
) -> int | None:
    normalized = value.strip()

    if not normalized:
        return None

    try:
        return int(
            normalized
        )
    except ValueError:
        return None
