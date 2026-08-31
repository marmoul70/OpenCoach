#!/usr/bin/env python3

from __future__ import annotations

import json

from datetime import (
    datetime,
    timezone,
)
from pathlib import Path

from opencoach.backup import (
    BackupService,
)
from opencoach.database.session import (
    PROJECT_ROOT,
)


STATUS_PATH = (
    PROJECT_ROOT
    / "data"
    / "backups"
    / "backup-status.json"
)


def write_status(
    *,
    status: str,
    filename: str | None,
    error: str | None,
) -> None:
    STATUS_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    payload = {
        "status": status,
        "executed_at": (
            datetime.now(
                timezone.utc
            ).isoformat()
        ),
        "filename": filename,
        "error": error,
    }

    temporary = STATUS_PATH.with_suffix(
        ".tmp"
    )

    temporary.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    temporary.replace(
        STATUS_PATH
    )


def main() -> None:
    service = BackupService()

    try:
        backup = (
            service.create_backup()
        )

    except Exception as exc:
        write_status(
            status="failed",
            filename=None,
            error=str(exc),
        )

        print(
            "ERREUR sauvegarde OpenCoach : "
            f"{exc}"
        )

        raise

    write_status(
        status="success",
        filename=backup.filename,
        error=None,
    )

    print(
        "Sauvegarde créée : "
        f"{backup.path}"
    )


if __name__ == "__main__":
    main()
