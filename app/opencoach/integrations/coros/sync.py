from __future__ import annotations

import json
import math
from calendar import monthrange
from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from opencoach.database.models import CorosDailyData
from opencoach.database.repositories import SqlWellnessRepository
from opencoach.integrations.coros.activity_mapper import upsert_coros_activity
from opencoach.integrations.coros.client import CorosMcpClient
from opencoach.integrations.coros.wellness_mapper import (
    map_coros_health_check_time_series,
    map_coros_hrv_time_series,
    map_coros_stress_time_series,
    map_coros_wellness_report,
)


DATE_KEYS = ("date", "day", "metricDate", "startDate", "wakeDate", "recordDate")
CATEGORY_TO_TOOL = {
    "daily_health": "queryDailyHealthData",
    "sleep": "querySleepOverview",
    "hrv": "querySleepHrv",
    "heart_rate": "queryAvgHeartRate",
    "resting_heart_rate": "queryRestingHeartRate",
    "stress": "queryStressLevel",
    "stress_timeseries": "queryStressTimeSeries",
    "health_check": "queryHealthCheckTimeSeries",
    "training_load": "queryTrainingLoadAssessment",
}

def months_ago(day: date, months: int) -> date:
    if months < 0:
        raise ValueError("Le nombre de mois ne peut pas être négatif.")
    month_index = day.year * 12 + day.month - 1 - months
    year, month_zero_based = divmod(month_index, 12)
    month = month_zero_based + 1
    return day.replace(year=year, month=month, day=min(day.day, monthrange(year, month)[1]))


def six_months_ago(day: date) -> date:
    return months_ago(day, 6)


def _jsonable(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    return str(value)


def _decode_text_payload(raw: str) -> Any:
    """Décode un JSON MCP éventuellement entouré de texte ou de fences."""
    candidate = raw.strip()
    if candidate.startswith("```"):
        candidate = candidate.split("\n", 1)[-1]
        if candidate.endswith("```"):
            candidate = candidate[:-3].strip()
    try:
        return json.loads(candidate)
    except (TypeError, ValueError):
        pass

    # Certains serveurs MCP préfixent le JSON d'un court texte explicatif.
    # On ne conserve que le premier objet/tableau JSON complet et valide.
    for index, char in enumerate(candidate):
        if char not in "[{":
            continue
        try:
            return json.JSONDecoder().raw_decode(candidate[index:])[0]
        except ValueError:
            continue
    return {"text": raw}


def _decode_tool_result(result: dict[str, Any]) -> Any:
    structured = result.get("structuredContent")
    if structured is not None:
        return _jsonable(structured)
    content = result.get("content")
    if isinstance(content, list):
        decoded = []
        for item in content:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                decoded.append(_decode_text_payload(item["text"]))
            else:
                decoded.append(_jsonable(item))
        if len(decoded) == 1:
            return decoded[0]
        return decoded
    return _jsonable(result)



def _parse_coros_sport_records_text(raw: str) -> list[dict[str, Any]]:
    """Convertit le rapport texte de querySportRecords en activités normalisées."""
    import re

    records: list[dict[str, Any]] = []
    blocks = re.split(r"(?m)^\s*\d+\.\s+", raw.strip())
    for block in blocks[1:]:
        lines = block.strip().splitlines()
        if not lines:
            continue
        title = re.match(r"(.+?)\s+[—-]\s+(\d{4}-\d{2}-\d{2})$", lines[0].strip())
        if not title:
            continue
        record: dict[str, Any] = {"name": title.group(1).strip(), "date": title.group(2)}

        def capture(pattern: str) -> re.Match[str] | None:
            return re.search(pattern, block, re.IGNORECASE)

        fields = {
            "labelId": r"\bLabelId\s*:\s*(\d+)",
            "sportType": r"\bSportType\s*:\s*(\d+)",
            "startTimestamp": r"\bstartTimestamp\s*=\s*(\d+)",
            "endTimestamp": r"\bendTimestamp\s*=\s*(\d+)",
            "avgHr": r"\bAvg HR\s*:\s*(\d+)\s*bpm",
            "maxHr": r"\bMax HR\s*:\s*(\d+)\s*bpm",
            "calories": r"\bCalories\s*:\s*(\d+)\s*kcal",
        }
        for key, pattern in fields.items():
            match = capture(pattern)
            if match:
                record[key] = int(match.group(1))

        duration = capture(r"\bDuration\s*:\s*(\d+):(\d{2})(?::(\d{2}))?")
        if duration:
            parts = [int(part) for part in duration.groups() if part is not None]
            if len(parts) == 3:
                record["workoutTime"] = parts[0] * 3600 + parts[1] * 60 + parts[2]
            else:
                record["workoutTime"] = parts[0] * 60 + parts[1]

        distance = capture(r"\bDistance\s*:\s*([\d.]+)\s*km")
        if distance:
            record["distanceMeters"] = float(distance.group(1)) * 1000
        else:
            distance = capture(r"\bDistance\s*:\s*([\d.]+)\s*m(?:\s|$)")
            if distance:
                record["distanceMeters"] = float(distance.group(1))

        pace = capture(r"\bAverage Pace\s*:\s*(\d+):(\d{2})\s*/km")
        if pace:
            pace_seconds = int(pace.group(1)) * 60 + int(pace.group(2))
            record["averagePaceSecondsPerKm"] = pace_seconds
            if pace_seconds > 0:
                record["average_speed_mps"] = 1000 / pace_seconds

        speed = capture(r"\bAverage Speed\s*:\s*([\d.]+)\s*km/h")
        if speed:
            record["average_speed_mps"] = float(speed.group(1)) / 3.6

        location = capture(r"\bLocation\s*:\s*([^\r\n]+)")
        if location:
            record["location"] = location.group(1).strip()

        coordinates = capture(r"\bStart Coordinates\s*:\s*([-+\d.]+)\s*,\s*([-+\d.]+)")
        if coordinates:
            record["startLatitude"] = float(coordinates.group(1))
            record["startLongitude"] = float(coordinates.group(2))

        if record.get("labelId") and record.get("startTimestamp") and record.get("sportType") is not None:
            records.append(record)
    return records


def _find_rows(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, str):
        decoded = _decode_text_payload(value)
        if isinstance(decoded, dict) and set(decoded) == {"text"}:
            return _parse_coros_sport_records_text(value)
        return _find_rows(decoded)
    if isinstance(value, list):
        rows = [item for item in value if isinstance(item, dict)]
        if rows:
            return rows
        for item in value:
            found = _find_rows(item)
            if found:
                return found
    if isinstance(value, dict):
        if isinstance(value.get("text"), str) and set(value) == {"text"}:
            return _parse_coros_sport_records_text(value["text"])
        for key in ("records", "list", "data", "items", "days", "dailyData", "sleepList", "result"):
            child = value.get(key)
            if isinstance(child, (dict, list, str)):
                found = _find_rows(child)
                if found:
                    return found
        if any(key in value for key in DATE_KEYS) or any(
            key in value for key in ("labelId", "label_id", "startTimestamp")
        ):
            return [value]
    return []


def _row_date(row: dict[str, Any], fallback: date) -> date:
    for key in DATE_KEYS:
        value = row.get(key)
        if isinstance(value, str):
            candidate = value.strip()
            for fmt in ("%Y%m%d", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"):
                try:
                    return datetime.strptime(candidate[:26], fmt).date()
                except ValueError:
                    continue
        if isinstance(value, (int, float)) and value > 10_000_000:
            try:
                return datetime.fromtimestamp(value / (1000 if value > 10_000_000_000 else 1), timezone.utc).date()
            except (OverflowError, OSError, ValueError):
                pass
    return fallback


def _upsert_snapshot(db: Session, profile_id: UUID, metric_date: date, category: str, payload: Any) -> None:
    row = db.scalar(select(CorosDailyData).where(
        CorosDailyData.athlete_profile_id == profile_id,
        CorosDailyData.metric_date == metric_date,
        CorosDailyData.category == category,
    ))
    normalized = payload if isinstance(payload, dict) else {"data": payload}
    if row is None:
        row = CorosDailyData(
            athlete_profile_id=profile_id,
            metric_date=metric_date,
            category=category,
            payload=normalized,
        )
        db.add(row)
    else:
        row.payload = normalized
        row.imported_at = datetime.now(timezone.utc)


def _upsert_activity_snapshot(
    db: Session,
    profile_id: UUID,
    metric_date: date,
    payload: dict[str, Any],
) -> None:
    """Conserve toutes les activités d'une journée dans un snapshot unique."""
    row = db.scalar(select(CorosDailyData).where(
        CorosDailyData.athlete_profile_id == profile_id,
        CorosDailyData.metric_date == metric_date,
        CorosDailyData.category == "activities",
    ))
    normalized = dict(payload)
    stored_payload = row.payload if row is not None and isinstance(row.payload, dict) else {}

    # Les anciennes versions stockaient une seule activité directement dans
    # payload. La convertir à la volée évite toute migration et préserve l'historique.
    stored_activities = stored_payload.get("activities")
    if isinstance(stored_activities, list):
        activities = [item for item in stored_activities if isinstance(item, dict)]
    elif stored_payload:
        activities = [stored_payload]
    else:
        activities = []

    activity_id = normalized.get("labelId") or normalized.get("label_id")
    existing_index = next(
        (
            index
            for index, item in enumerate(activities)
            if activity_id is not None
            and str(item.get("labelId") or item.get("label_id")) == str(activity_id)
        ),
        None,
    )
    if existing_index is None:
        activities.append(normalized)
    else:
        activities[existing_index] = normalized

    if row is None:
        row = CorosDailyData(
            athlete_profile_id=profile_id,
            metric_date=metric_date,
            category="activities",
            payload={"activities": activities},
        )
        db.add(row)
        # SessionLocal utilise autoflush=False : sans flush explicite, une
        # seconde activité du même jour ne voit pas ce snapshot encore pending
        # et tente d'insérer une deuxième ligne avec la même clé unique.
        db.flush()
    else:
        row.payload = {"activities": activities}
        row.imported_at = datetime.now(timezone.utc)



def _build_tool_arguments(
    tool: dict[str, Any],
    available_values: dict[str, Any],
) -> dict[str, Any] | None:
    """Construit les arguments à partir du schéma MCP réellement annoncé."""
    schema = tool.get("inputSchema")
    if not isinstance(schema, dict):
        return None
    properties = schema.get("properties")
    if not isinstance(properties, dict):
        return None
    normalize_key = lambda value: "".join(char for char in str(value).casefold() if char.isalnum())
    normalized_values = {normalize_key(key): value for key, value in available_values.items()}
    required = schema.get("required", [])
    if not isinstance(required, list):
        return None
    arguments: dict[str, Any] = {}
    for property_name, definition in properties.items():
        if not isinstance(definition, dict):
            continue
        value = normalized_values.get(normalize_key(property_name))
        if value is None:
            if property_name in required:
                return None
            continue
        expected_type = definition.get("type")
        if isinstance(expected_type, list):
            expected_type = next(
                (item for item in expected_type if item != "null"), None
            )
        try:
            if expected_type == "string":
                value = str(value)
            elif expected_type == "integer":
                if isinstance(value, bool):
                    return None
                if isinstance(value, float) and not value.is_integer():
                    return None
                value = int(value)
            elif expected_type == "number":
                if isinstance(value, bool):
                    return None
                value = float(value)
                if not math.isfinite(value):
                    return None
            elif expected_type == "boolean":
                if isinstance(value, bool):
                    pass
                elif value in (0, 1):
                    value = bool(value)
                elif isinstance(value, str) and value.strip().casefold() in {"true", "false"}:
                    value = value.strip().casefold() == "true"
                else:
                    return None
        except (TypeError, ValueError, OverflowError):
            return None
        arguments[property_name] = value
    if any(key not in arguments for key in required):
        return None
    return arguments

class CorosImportService:
    """Import incrémental, idempotent et reprenable des données COROS."""

    def __init__(self, client: CorosMcpClient, db: Session, profile_id: UUID, *, progress_callback: Callable[[str, str | None], None] | None = None):
        self.client = client
        self.db = db
        self.profile_id = profile_id
        self.progress_callback = progress_callback

    def _checkpoint(self, category: str, next_date: date | None) -> None:
        if self.progress_callback:
            self.progress_callback(category, next_date.isoformat() if next_date else None)

    def import_history(
        self,
        categories: dict[str, bool],
        *,
        months: int = 6,
        today: date | None = None,
        start_date: date | None = None,
        checkpoint: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        end = today or datetime.now(timezone.utc).date()
        start = start_date or months_ago(end, months)
        if start > end:
            raise ValueError("La date de début de l'import COROS dépasse la date de fin.")
        tool_definitions = {
            item.get("name"): item
            for item in self.client.list_tools()
            if item.get("name")
        }
        tools = set(tool_definitions)
        imported: dict[str, int] = {}
        skipped: list[str] = []

        saved = checkpoint or {}
        if categories.get("activities", True) and "activities" not in saved.get("_completed", "").split(","):
            if "querySportRecords" not in tools:
                skipped.append("activities:outil_non_disponible")
            else:
                imported["activities"] = self._import_activities(start, end, tool_definitions, categories, saved.get("activities"))

        for category, enabled in categories.items():
            if not enabled or category in {"activities", "activity_details", "fit_files"}:
                continue
            tool_name = CATEGORY_TO_TOOL.get(category)
            if not tool_name:
                continue
            if tool_name not in tools:
                skipped.append(f"{category}:outil_non_disponible")
                continue
            if category in saved.get("_completed", "").split(","):
                continue
            imported[category] = self._import_daily_category(category, tool_name, start, end, saved.get(category))

        self.db.commit()
        return {
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "imported_snapshots": imported,
            "skipped": skipped,
        }

    def _call_and_store(self, tool_name: str, arguments: dict[str, Any], category: str, fallback: date) -> int:
        raw = _decode_tool_result(self.client.call_tool(tool_name, arguments))
        if raw is None or raw == [] or raw == {}:
            return 0
        rows = _find_rows(raw)
        if not rows:
            rows = [{"data": raw}]
        count = 0
        for item in rows:
            metric_date = _row_date(item, fallback)
            _upsert_snapshot(self.db, self.profile_id, metric_date, category, item)

            series_parsers = {
                "hrv": ("hrv_timeseries", map_coros_hrv_time_series),
                "stress_timeseries": ("stress_points", map_coros_stress_time_series),
                "health_check": (
                    "health_check_points",
                    map_coros_health_check_time_series,
                ),
            }
            series_definition = series_parsers.get(category)
            if series_definition is not None:
                snapshot_category, parser = series_definition
                samples = parser(item)
                if samples:
                    _upsert_snapshot(
                        self.db,
                        self.profile_id,
                        metric_date,
                        snapshot_category,
                        {
                            "source_category": category,
                            "samples": [
                                {
                                    "metric": sample.metric,
                                    "measured_at": sample.measured_at.isoformat(),
                                    "value": sample.value,
                                    "unit": sample.unit,
                                    "source_timezone": sample.source_timezone,
                                    "status": sample.status,
                                    "confidence": sample.confidence,
                                    "score": sample.score,
                                    "metadata": sample.metadata,
                                }
                                for sample in samples
                            ],
                        },
                    )

            if category in {
                "daily_health",
                "sleep",
                "hrv",
                "heart_rate",
                "resting_heart_rate",
                "stress",
                "stress_timeseries",
                "health_check",
                "training_load",
            }:
                wellness_days = map_coros_wellness_report(category, item, metric_date)
                wellness_repository = SqlWellnessRepository(self.db)
                for mapped in wellness_days:
                    existing = wellness_repository.get_by_date(
                        self.profile_id, mapped.date, provider="coros"
                    )
                    if existing is not None:
                        # Fusion non destructive : plusieurs catégories alimentent une journée.
                        for field in (
                            "fitness_ctl", "fatigue_atl", "ramp_rate", "resting_hr",
                            "avg_hr", "min_hr", "max_hr",
                            "hrv", "hrv_baseline", "stress_avg",
                            "sleep_seconds", "sleep_score", "sleep_quality",
                            "sleep_deep_seconds", "sleep_light_seconds",
                            "sleep_rem_seconds", "sleep_awake_seconds",
                            "avg_sleeping_hr", "min_sleeping_hr", "max_sleeping_hr",
                            "spo2", "steps", "provider_updated_at",
                        ):
                            if getattr(mapped, field) is None:
                                setattr(mapped, field, getattr(existing, field))

                    has_metrics = any(
                        getattr(mapped, field) is not None
                        for field in (
                            "fitness_ctl", "fatigue_atl", "ramp_rate", "resting_hr",
                            "avg_hr", "min_hr", "max_hr",
                            "hrv", "hrv_baseline", "stress_avg",
                            "sleep_seconds", "sleep_score", "sleep_quality",
                            "sleep_deep_seconds", "sleep_light_seconds",
                            "sleep_rem_seconds", "sleep_awake_seconds",
                            "avg_sleeping_hr", "min_sleeping_hr", "max_sleeping_hr",
                            "spo2", "steps",
                        )
                    )
                    if has_metrics:
                        wellness_repository.save_wellness_day(self.profile_id, mapped)
            count += 1
        return count

    def _import_daily_category(self, category: str, tool_name: str, start: date, end: date, resume_date: str | None = None) -> int:
        count = 0
        if category in {"daily_health", "resting_heart_rate", "stress", "training_load"}:
            # Ces endpoints exposent une fenêtre glissante récente uniquement.
            count = self._call_and_store(tool_name, {"days": 7}, category, end)
            self.db.commit()
            self._checkpoint(category, None)
            return count

        cursor = max(start, date.fromisoformat(resume_date)) if resume_date else start
        while cursor <= end:
            window_end = min(cursor + timedelta(days=6), end)
            args = {"startDate": cursor.strftime("%Y%m%d"), "endDate": window_end.strftime("%Y%m%d")}
            if category in {"stress_timeseries", "health_check"}:
                args["days"] = (window_end - cursor).days + 1
            count += self._call_and_store(tool_name, args, category, cursor)
            cursor = window_end + timedelta(days=1)
            self.db.commit()
            self._checkpoint(category, cursor if cursor <= end else None)
        return count

    def _import_activities(self, start: date, end: date, tool_definitions: dict[str, dict[str, Any]], categories: dict[str, bool], resume_date: str | None = None) -> int:
        count = 0
        cursor = max(start, date.fromisoformat(resume_date)) if resume_date else start
        while cursor <= end:
            window_end = min(cursor + timedelta(days=6), end)
            available_values = {
                "startDate": cursor.strftime("%Y%m%d"),
                "endDate": window_end.strftime("%Y%m%d"),
                "limit": 100,
            }
            query_tool = tool_definitions.get("querySportRecords", {})
            arguments = _build_tool_arguments(query_tool, available_values)
            # Compatibilité avec les anciens serveurs MCP qui n'exposent pas
            # inputSchema dans tools/list. Si le schéma est présent, il reste
            # toujours la source de vérité pour les noms et types de paramètres.
            if arguments is None and not isinstance(query_tool.get("inputSchema"), dict):
                arguments = available_values
            if arguments is None:
                raise ValueError(
                    "Le schéma MCP querySportRecords ne permet pas de construire les paramètres."
                )
            raw = _decode_tool_result(
                self.client.call_tool("querySportRecords", arguments)
            )
            records = _find_rows(raw)
            for record in records:
                metric_date = _row_date(record, cursor)
                payload = dict(record)
                if categories.get("activity_details") and "getActivityDetail" in tool_definitions:
                    detail_arguments = _build_tool_arguments(
                        tool_definitions["getActivityDetail"],
                        {
                            "labelId": record.get("labelId") or record.get("label_id"),
                            "sportType": record.get("sportType") or record.get("sport_type"),
                        },
                    )
                    if detail_arguments is not None:
                        detail = _decode_tool_result(
                            self.client.call_tool("getActivityDetail", detail_arguments)
                        )
                        payload["activity_detail"] = detail
                if not upsert_coros_activity(self.db, self.profile_id, record):
                    continue
                _upsert_activity_snapshot(self.db, self.profile_id, metric_date, payload)
                count += 1
            cursor = window_end + timedelta(days=1)
            self.db.commit()
            self._checkpoint("activities", cursor if cursor <= end else None)
        # Aucun résultat activité : conserver le checkpoint initial pour
        # retenter toute la fenêtre au prochain lancement.
        if count == 0:
            self._checkpoint("activities", start)
        return count
