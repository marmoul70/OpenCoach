"""Stockage temporaire des propositions d'adaptation hebdomadaire.

Les propositions ne font pas partie du planning persistant : elles sont
conservées sous le répertoire temporaire système et supprimées à la
validation, au refus ou à la saisie manuelle d'une séance.
"""
from __future__ import annotations

import json
import os
import tempfile
from datetime import date
from pathlib import Path
from uuid import UUID


class WeeklyAdaptationProposalStore:
    """Stockage fichier isolé par profil et semaine."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = Path(root or tempfile.gettempdir()) / "opencoach" / "weekly-proposals"

    def _path(self, athlete_profile_id: UUID, week_start: date) -> Path:
        return self.root / str(athlete_profile_id) / f"{week_start.isoformat()}.json"

    def save(self, athlete_profile_id: UUID, week_start: date, payload: dict) -> Path:
        path = self._path(athlete_profile_id, week_start)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = path.with_suffix(".json.tmp")
        temporary_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        os.replace(temporary_path, path)
        return path

    def get(self, athlete_profile_id: UUID, week_start: date) -> dict | None:
        path = self._path(athlete_profile_id, week_start)
        if not path.is_file():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError("La proposition temporaire est illisible.") from exc
        if not isinstance(payload, dict):
            raise RuntimeError("La proposition temporaire est invalide.")
        return payload

    def delete(self, athlete_profile_id: UUID, week_start: date) -> bool:
        path = self._path(athlete_profile_id, week_start)
        try:
            path.unlink()
        except FileNotFoundError:
            return False
        parent = path.parent
        try:
            parent.rmdir()
        except OSError:
            pass
        return True
