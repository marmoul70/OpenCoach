from __future__ import annotations

import json
import sqlite3
import tempfile
import zipfile

from dataclasses import dataclass
from datetime import (
    datetime,
    timedelta,
    timezone,
)
from pathlib import Path

from sqlalchemy.engine import make_url

from opencoach.database.session import (
    DATABASE_URL,
    PROJECT_ROOT,
)


BACKUP_FORMAT_VERSION = 1

DEFAULT_BACKUP_DIRECTORY = (
    PROJECT_ROOT
    / "data"
    / "backups"
)


@dataclass(
    frozen=True,
    slots=True,
)
class BackupInfo:
    filename: str
    path: Path
    created_at: datetime
    size_bytes: int


class BackupService:
    """Gestion des sauvegardes SQLite OpenCoach."""

    def __init__(
        self,
        *,
        database_url: str = DATABASE_URL,
        backup_directory: Path = (
            DEFAULT_BACKUP_DIRECTORY
        ),
        retention_days: int = 7,
    ) -> None:
        self.database_url = (
            database_url
        )

        self.backup_directory = (
            backup_directory
        )

        self.retention_days = (
            retention_days
        )

    def create_backup(
        self,
    ) -> BackupInfo:
        source_path = (
            self._database_path()
        )

        self.backup_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        created_at = datetime.now(
            timezone.utc
        )

        timestamp = (
            created_at.strftime(
                "%Y-%m-%d_%H%M%S"
            )
        )

        filename = (
            f"opencoach-{timestamp}.zip"
        )

        destination = (
            self.backup_directory
            / filename
        )

        with tempfile.TemporaryDirectory() as raw_tmp:
            temp_directory = Path(
                raw_tmp
            )

            database_copy = (
                temp_directory
                / "opencoach.db"
            )

            self._copy_sqlite_database(
                source_path=source_path,
                destination_path=(
                    database_copy
                ),
            )

            manifest = {
                "format_version": (
                    BACKUP_FORMAT_VERSION
                ),
                "application": (
                    "OpenCoach"
                ),
                "created_at": (
                    created_at.isoformat()
                ),
                "database": (
                    "opencoach.db"
                ),
            }

            manifest_path = (
                temp_directory
                / "manifest.json"
            )

            manifest_path.write_text(
                json.dumps(
                    manifest,
                    indent=2,
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )

            with zipfile.ZipFile(
                destination,
                mode="w",
                compression=(
                    zipfile.ZIP_DEFLATED
                ),
            ) as archive:
                archive.write(
                    database_copy,
                    arcname="opencoach.db",
                )

                archive.write(
                    manifest_path,
                    arcname="manifest.json",
                )

        self.cleanup_old_backups()

        return self._to_backup_info(
            destination
        )

    def list_backups(
        self,
    ) -> list[BackupInfo]:
        if (
            not self.backup_directory.exists()
        ):
            return []

        backups = [
            self._to_backup_info(
                path
            )
            for path
            in self.backup_directory.glob(
                "opencoach-*.zip"
            )
            if path.is_file()
        ]

        return sorted(
            backups,
            key=lambda backup: (
                backup.created_at
            ),
            reverse=True,
        )

    def cleanup_old_backups(
        self,
    ) -> int:
        cutoff = (
            datetime.now(
                timezone.utc
            )
            - timedelta(
                days=self.retention_days
            )
        )

        deleted = 0

        for backup in self.list_backups():
            if backup.created_at >= cutoff:
                continue

            backup.path.unlink(
                missing_ok=True
            )

            deleted += 1

        return deleted

    def get_backup_path(
        self,
        filename: str,
    ) -> Path:
        safe_filename = Path(
            filename
        ).name

        if (
            safe_filename != filename
            or not safe_filename.endswith(
                ".zip"
            )
        ):
            raise ValueError(
                "Nom de sauvegarde invalide."
            )

        path = (
            self.backup_directory
            / safe_filename
        )

        if not path.is_file():
            raise FileNotFoundError(
                safe_filename
            )

        return path

    def _database_path(
        self,
    ) -> Path:
        url = make_url(
            self.database_url
        )

        if (
            url.get_backend_name()
            != "sqlite"
        ):
            raise RuntimeError(
                "Le système de sauvegarde "
                "actuel nécessite SQLite."
            )

        database = url.database

        if (
            database is None
            or database == ":memory:"
        ):
            raise RuntimeError(
                "La base SQLite doit être "
                "stockée dans un fichier."
            )

        path = Path(
            database
        )

        if not path.is_file():
            raise FileNotFoundError(
                path
            )

        return path

    @staticmethod
    def _copy_sqlite_database(
        *,
        source_path: Path,
        destination_path: Path,
    ) -> None:
        source = sqlite3.connect(
            source_path
        )

        destination = sqlite3.connect(
            destination_path
        )

        try:
            source.backup(
                destination
            )

            destination.execute(
                "PRAGMA wal_checkpoint(FULL)"
            )

            destination.commit()

        finally:
            destination.close()
            source.close()

    @staticmethod
    def _to_backup_info(
        path: Path,
    ) -> BackupInfo:
        stat = path.stat()

        return BackupInfo(
            filename=path.name,
            path=path,
            created_at=datetime.fromtimestamp(
                stat.st_mtime,
                tz=timezone.utc,
            ),
            size_bytes=stat.st_size,
        )
