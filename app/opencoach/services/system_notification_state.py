from __future__ import annotations

import json
from pathlib import Path

from opencoach.database.session import (
    PROJECT_ROOT,
)


STATE_PATH = (
    PROJECT_ROOT
    / "data"
    / "notifications"
    / "system-alerts.json"
)


class SystemNotificationState:
    """État persistant des alertes système OpenCoach."""

    def __init__(
        self,
        path: Path = STATE_PATH,
    ) -> None:
        self.path = path

    def should_notify(
        self,
        event: str,
    ) -> bool:
        """Retourne True uniquement au premier échec."""

        state = self._read()

        return not bool(
            state.get(
                event,
                False,
            )
        )

    def mark_failed(
        self,
        event: str,
    ) -> None:
        state = self._read()

        state[event] = True

        self._write(
            state
        )

    def mark_success(
        self,
        event: str,
    ) -> None:
        state = self._read()

        if not state.get(
            event,
            False,
        ):
            return

        state[event] = False

        self._write(
            state
        )

    def _read(
        self,
    ) -> dict[str, bool]:
        if not self.path.exists():
            return {}

        try:
            raw = json.loads(
                self.path.read_text(
                    encoding="utf-8",
                )
            )

        except (
            OSError,
            json.JSONDecodeError,
        ):
            return {}

        if not isinstance(
            raw,
            dict,
        ):
            return {}

        return {
            str(key):
                bool(value)
            for key, value
            in raw.items()
        }

    def _write(
        self,
        state: dict[str, bool],
    ) -> None:
        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary = (
            self.path
            .with_suffix(
                ".tmp"
            )
        )

        temporary.write_text(
            json.dumps(
                state,
                indent=2,
                ensure_ascii=False,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

        temporary.replace(
            self.path
        )
