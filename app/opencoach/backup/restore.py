from __future__ import annotations

import json
import sqlite3
import tempfile
import threading
import zipfile

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.engine import make_url

from opencoach.database.session import (
    DATABASE_URL,
)

from .service import (
    BACKUP_FORMAT_VERSION,
    BackupInfo,
    BackupService,
)


MAX_BACKUP_SIZE_BYTES = (
    100
    * 1024
    * 1024
)


_RESTORE_LOCK = threading.Lock()


@dataclass(
    frozen=True,
    slots=True,
)
class BackupRestoreResult:
    """Résultat d'une restauration OpenCoach."""

    safety_backup: BackupInfo
    imported_revision: str


class BackupRestoreService:
    """Validation et restauration sécurisée d'un backup."""

    def __init__(
        self,
        *,
        backup_service: BackupService | None = None,
        database_url: str = DATABASE_URL,
    ) -> None:
        self.backup_service = (
            backup_service
            or BackupService()
        )

        self.database_url = (
            database_url
        )


    def restore_archive_bytes(
        self,
        archive_bytes: bytes,
    ) -> BackupRestoreResult:
        if not _RESTORE_LOCK.acquire(
            blocking=False
        ):
            raise RuntimeError(
                "Une restauration OpenCoach "
                "est déjà en cours."
            )

        try:
            return self._restore_archive_bytes_locked(
                archive_bytes
            )

        finally:
            _RESTORE_LOCK.release()


    def _restore_archive_bytes_locked(
        self,
        archive_bytes: bytes,
    ) -> BackupRestoreResult:
        if not archive_bytes:
            raise ValueError(
                "La sauvegarde importée est vide."
            )

        if (
            len(archive_bytes)
            > MAX_BACKUP_SIZE_BYTES
        ):
            raise ValueError(
                "La sauvegarde dépasse "
                "la limite de 100 Mo."
            )

        with tempfile.TemporaryDirectory() as raw_tmp:
            directory = Path(
                raw_tmp
            )

            archive_path = (
                directory
                / "backup.zip"
            )

            archive_path.write_bytes(
                archive_bytes
            )

            imported_database = (
                directory
                / "opencoach-import.db"
            )

            self._extract_and_validate_archive(
                archive_path=archive_path,
                database_path=imported_database,
            )

            self._validate_sqlite_database(
                imported_database
            )

            active_database = (
                self._database_path()
            )

            imported_revision = (
                self._alembic_revision(
                    imported_database
                )
            )

            current_revision = (
                self._alembic_revision(
                    active_database
                )
            )

            if (
                imported_revision
                != current_revision
            ):
                raise ValueError(
                    "Version de base incompatible : "
                    f"backup={imported_revision}, "
                    f"OpenCoach={current_revision}."
                )

            safety_backup = (
                self.backup_service
                .create_backup()
            )

            try:
                self._restore_sqlite_database(
                    source_path=imported_database,
                    destination_path=active_database,
                )

                self._validate_sqlite_database(
                    active_database
                )

            except Exception as restore_error:
                try:
                    self._rollback_from_backup(
                        backup_path=(
                            safety_backup.path
                        ),
                        destination_path=(
                            active_database
                        ),
                    )

                    self._validate_sqlite_database(
                        active_database
                    )

                except Exception as rollback_error:
                    raise RuntimeError(
                        "La restauration a échoué "
                        "ET le rollback automatique "
                        "de la base précédente a échoué. "
                        "La sauvegarde de sécurité est : "
                        f"{safety_backup.filename}"
                    ) from rollback_error

                raise RuntimeError(
                    "La restauration a échoué. "
                    "La base précédente a été "
                    "restaurée automatiquement. "
                    "Sauvegarde de sécurité : "
                    f"{safety_backup.filename}"
                ) from restore_error

            return BackupRestoreResult(
                safety_backup=(
                    safety_backup
                ),
                imported_revision=(
                    imported_revision
                ),
            )


    def restore_existing_backup(
        self,
        filename: str,
    ) -> BackupRestoreResult:
        path = (
            self.backup_service
            .get_backup_path(
                filename
            )
        )

        return self.restore_archive_bytes(
            path.read_bytes()
        )


    def _rollback_from_backup(
        self,
        *,
        backup_path: Path,
        destination_path: Path,
    ) -> None:
        """Restaure la DB précédant une restauration échouée."""

        with tempfile.TemporaryDirectory() as raw_tmp:
            directory = Path(
                raw_tmp
            )

            rollback_database = (
                directory
                / "rollback.db"
            )

            self._extract_and_validate_archive(
                archive_path=backup_path,
                database_path=rollback_database,
            )

            self._validate_sqlite_database(
                rollback_database
            )

            self._restore_sqlite_database(
                source_path=rollback_database,
                destination_path=destination_path,
            )


    def _extract_and_validate_archive(
        self,
        *,
        archive_path: Path,
        database_path: Path,
    ) -> None:
        try:
            with zipfile.ZipFile(
                archive_path,
                mode="r",
            ) as archive:
                names = set(
                    archive.namelist()
                )

                expected = {
                    "opencoach.db",
                    "manifest.json",
                }

                if not expected.issubset(
                    names
                ):
                    raise ValueError(
                        "Archive OpenCoach invalide : "
                        "opencoach.db ou "
                        "manifest.json absent."
                    )

                manifest_bytes = (
                    archive.read(
                        "manifest.json"
                    )
                )

                try:
                    manifest = json.loads(
                        manifest_bytes.decode(
                            "utf-8"
                        )
                    )

                except (
                    UnicodeDecodeError,
                    json.JSONDecodeError,
                ) as exc:
                    raise ValueError(
                        "Le manifest de sauvegarde "
                        "est invalide."
                    ) from exc

                if (
                    manifest.get(
                        "application"
                    )
                    != "OpenCoach"
                ):
                    raise ValueError(
                        "Cette archive n'est pas "
                        "une sauvegarde OpenCoach."
                    )

                if (
                    manifest.get(
                        "format_version"
                    )
                    != BACKUP_FORMAT_VERSION
                ):
                    raise ValueError(
                        "Version du format de "
                        "sauvegarde incompatible."
                    )

                database_path.write_bytes(
                    archive.read(
                        "opencoach.db"
                    )
                )

        except zipfile.BadZipFile as exc:
            raise ValueError(
                "Le fichier fourni n'est "
                "pas un ZIP valide."
            ) from exc


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
                "La restauration automatique "
                "nécessite actuellement SQLite."
            )

        database = url.database

        if (
            database is None
            or database == ":memory:"
        ):
            raise RuntimeError(
                "La base SQLite active "
                "n'est pas un fichier."
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
    def _validate_sqlite_database(
        path: Path,
    ) -> None:
        connection = sqlite3.connect(
            f"file:{path}?mode=ro",
            uri=True,
        )

        try:
            result = connection.execute(
                "PRAGMA integrity_check"
            ).fetchone()

            if (
                result is None
                or result[0] != "ok"
            ):
                raise ValueError(
                    "La base SQLite est "
                    "corrompue."
                )

            violations = (
                connection.execute(
                    "PRAGMA foreign_key_check"
                ).fetchall()
            )

            if violations:
                raise ValueError(
                    "La base contient des "
                    "violations de clés étrangères."
                )

        finally:
            connection.close()


    @staticmethod
    def _alembic_revision(
        path: Path,
    ) -> str:
        connection = sqlite3.connect(
            f"file:{path}?mode=ro",
            uri=True,
        )

        try:
            try:
                row = connection.execute(
                    """
                    SELECT version_num
                    FROM alembic_version
                    LIMIT 1
                    """
                ).fetchone()

            except sqlite3.DatabaseError as exc:
                raise ValueError(
                    "Version Alembic "
                    "introuvable."
                ) from exc

        finally:
            connection.close()

        if row is None:
            raise ValueError(
                "Version Alembic introuvable."
            )

        return str(
            row[0]
        )


    @staticmethod
    def _restore_sqlite_database(
        *,
        source_path: Path,
        destination_path: Path,
    ) -> None:
        source = sqlite3.connect(
            f"file:{source_path}?mode=ro",
            uri=True,
        )

        destination = sqlite3.connect(
            destination_path,
            timeout=30,
        )

        try:
            source.backup(
                destination
            )

            destination.commit()

        except sqlite3.DatabaseError as exc:
            raise RuntimeError(
                "Impossible de restaurer "
                "la base OpenCoach."
            ) from exc

        finally:
            destination.close()
            source.close()
