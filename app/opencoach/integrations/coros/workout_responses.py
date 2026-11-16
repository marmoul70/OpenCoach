"""Parsing des réponses MCP COROS relatives au calendrier et aux séances."""

from __future__ import annotations

import json
import re
from typing import Any


def _extract_coros_scheduled_id(result: dict[str, Any]) -> str | None:
    """Récupère idInPlan sans dépendre d'un format de réponse unique."""
    candidates: list[Any] = []
    schedule_texts: list[str] = []
    structured = result.get("structuredContent")
    if structured is not None:
        candidates.append(structured)

    for item in result.get("content", []):
        if not isinstance(item, dict) or item.get("type") != "text":
            continue
        raw_text = item.get("text")
        if not isinstance(raw_text, str):
            continue
        try:
            candidates.append(json.loads(raw_text))
        except ValueError:
            object_start = raw_text.find("{")
            object_end = raw_text.rfind("}")
            if object_start >= 0 and object_end > object_start:
                try:
                    candidates.append(
                        json.loads(raw_text[object_start:object_end + 1])
                    )
                except ValueError:
                    pass

    for candidate in candidates:
        found = _find_coros_id(candidate)
        if found:
            return found
    return None


def _extract_coros_scheduled_details(
    result: dict[str, Any],
) -> dict[str, Any] | None:
    """Extrait l'état d'éditabilité d'une séance standalone COROS."""
    candidates: list[Any] = []
    schedule_texts: list[str] = []
    structured = result.get("structuredContent")
    if structured is not None:
        candidates.append(structured)

    for item in result.get("content", []):
        # COROS MCP may return either text blocks or direct string items.
        if isinstance(item, str):
            raw_text = item
        elif isinstance(item, dict) and item.get("type") == "text":
            raw_text = item.get("text")
        else:
            continue
        if not isinstance(raw_text, str):
            continue
        try:
            decoded = json.loads(raw_text)
        except ValueError:
            decoded = None
        # Some MCP responses are JSON strings containing another JSON object.
        if isinstance(decoded, str):
            try:
                decoded = json.loads(decoded)
            except ValueError:
                pass
        if isinstance(decoded, (dict, list)):
            candidates.append(decoded)
        else:
            start = raw_text.find("{")
            end = raw_text.rfind("}")
            if start >= 0 and end > start:
                try:
                    candidates.append(json.loads(raw_text[start:end + 1]))
                except ValueError:
                    pass
        # Preserve decoded plain-text details; COROS returns editability and
        # the complete course JSON as labelled lines in this response format.
        schedule_texts.append(decoded if isinstance(decoded, str) else raw_text)

    for raw_text in schedule_texts:
        editable_match = re.search(
            r"^Editable via MCP:\s*(yes|no)\s*$",
            raw_text,
            re.IGNORECASE | re.MULTILINE,
        )
        course_match = re.search(
            r"^Course JSON:\s*(\{.*\})\s*$",
            raw_text,
            re.IGNORECASE | re.MULTILINE | re.DOTALL,
        )
        if editable_match:
            course = None
            if course_match:
                try:
                    parsed_course = json.loads(course_match.group(1))
                    if isinstance(parsed_course, dict):
                        course = parsed_course
                except ValueError:
                    pass
            candidates.append({
                "editable": editable_match.group(1).casefold() == "yes",
                "course": course,
            })

    def find_course(value: Any) -> dict[str, Any] | None:
        if isinstance(value, dict):
            course = value.get("course")
            if isinstance(course, dict):
                return course
            if "courseName" in value and isinstance(value.get("sections"), list):
                return value
            for child in value.values():
                found = find_course(child)
                if found is not None:
                    return found
        elif isinstance(value, list):
            for child in value:
                found = find_course(child)
                if found is not None:
                    return found
        return None

    def find_editability(value: Any) -> tuple[bool, str | None] | None:
        if isinstance(value, dict):
            editable = value.get("editable")
            if isinstance(editable, bool):
                reason = value.get("reason") or value.get("reasons") or value.get("message")
                normalized_reason = (
                    "; ".join(str(item) for item in reason)
                    if isinstance(reason, list)
                    else str(reason) if reason else None
                )
                return editable, normalized_reason
            for child in value.values():
                found = find_editability(child)
                if found is not None:
                    return found
        elif isinstance(value, list):
            for child in value:
                found = find_editability(child)
                if found is not None:
                    return found
        return None

    for candidate in candidates:
        editability = find_editability(candidate)
        if editability is not None:
            editable, reason = editability
            return {
                "editable": editable,
                "reason": reason,
                "course": find_course(candidate),
            }
    return None


def _extract_scheduled_workout_records_for_date(
    result: dict[str, Any],
    target_date,
    *,
    date_scoped: bool = False,
) -> list[tuple[str | None, str]]:
    """Extrait les séances d'une date, ou toutes celles d'une réponse déjà filtrée."""

    # All incoming COROS date representations are normalized by removing
    # hyphens before comparison, so keep the target in the same YYYYMMDD form.
    target_values = {
        target_date.strftime("%Y%m%d"),
        target_date.strftime("%Y-%m-%d"),
    }
    candidates: list[Any] = []
    schedule_texts: list[str] = []
    structured = result.get("structuredContent")
    if structured is not None:
        candidates.append(structured)
    for item in result.get("content", []):
        # MCP servers may return either standard text content blocks or a
        # direct list of strings (the latter is used by COROS schedule queries).
        if isinstance(item, str):
            raw_text = item
        elif isinstance(item, dict) and item.get("type") == "text":
            raw_text = item.get("text")
        else:
            continue
        if not isinstance(raw_text, str):
            continue
        # COROS MCP may wrap its plain-text report as a JSON string
        # (including escaped \\n sequences). Unwrap that layer before
        # parsing lines; parsing it only as a JSON candidate loses all rows.
        try:
            decoded_text = json.loads(raw_text)
        except ValueError:
            decoded_text = None
        if isinstance(decoded_text, str):
            raw_text = decoded_text
        elif isinstance(decoded_text, (dict, list)):
            candidates.append(decoded_text)
        else:
            object_start = raw_text.find("{")
            object_end = raw_text.rfind("}")
            if object_start >= 0 and object_end > object_start:
                try:
                    candidates.append(json.loads(raw_text[object_start:object_end + 1]))
                except ValueError:
                    pass
        # Preserve normalized text for the line-oriented schedule parser.
        schedule_texts.append(raw_text)

    date_keys = {
        "date", "day", "happenDay", "happen_day",
        "scheduleDate", "schedule_date",
    }
    workout_list_keys = {
        "courses", "workouts", "entities", "programs",
        "scheduledWorkouts", "scheduled_workouts", "items",
    }
    found: list[tuple[str | None, str]] = []

    # COROS MCP currently renders the schedule as plain text. Parse its
    # date/name/idInPlan blocks as well as structured JSON responses.
    for raw_text in schedule_texts:
        current_date = None
        current_name = None
        for raw_line in raw_text.splitlines():
            line = raw_line.strip()
            date_match = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", line)
            if date_match:
                current_date = "".join(date_match.groups())
                current_name = None
                continue
            if not line:
                continue
            id_match = re.fullmatch(r"idInPlan\s*:\s*(\d+)", line, re.IGNORECASE)
            if id_match:
                if (date_scoped or current_date in target_values) and current_name:
                    record = (id_match.group(1), current_name)
                    if record not in found:
                        found.append(record)
                current_name = None
                continue
            if (
                (date_scoped or current_date is not None)
                and current_name is None
                and not line.startswith(("=", "-", "Training Schedule", "Plan ID:", "Standalone workout", "Distance:", "Estimated Time:", "Load:", "To view", "Use Plan ID"))
            ):
                current_name = line

    def collect(value: Any, *, in_workout_list: bool = False) -> None:
        if isinstance(value, dict):
            is_workout = in_workout_list or any(
                key in value
                for key in ("courseName", "workoutName", "idInPlan", "id_in_plan")
            )
            if is_workout:
                name = (
                    value.get("courseName")
                    or value.get("workoutName")
                    or value.get("name")
                    or value.get("title")
                )
                raw_id = value.get("idInPlan", value.get("id_in_plan"))
                if isinstance(name, str) and name.strip():
                    record = (
                        str(raw_id) if raw_id is not None else None,
                        name.strip(),
                    )
                    if record not in found:
                        found.append(record)
            for key, child in value.items():
                collect(child, in_workout_list=key in workout_list_keys)
        elif isinstance(value, list):
            for child in value:
                collect(child, in_workout_list=in_workout_list)

    def visit(value: Any, *, date_matches: bool = False) -> None:
        if isinstance(value, dict):
            matches_date = date_matches or any(
                str(value.get(key, "")).replace("-", "")[:8] in target_values
                for key in date_keys
                if value.get(key) is not None
            )
            if matches_date:
                for key, child in value.items():
                    if key in workout_list_keys:
                        collect(child, in_workout_list=True)
                if not any(key in value for key in workout_list_keys):
                    for child in value.values():
                        visit(child, date_matches=True)
                return
            for key, child in value.items():
                if str(key).replace("-", "")[:8] == target_date.strftime("%Y%m%d"):
                    collect(child, in_workout_list=True)
                else:
                    visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child, date_matches=date_matches)

    for candidate in candidates:
        visit(candidate, date_matches=date_scoped)
    return found



def _extract_standalone_scheduled_workout_records_for_date(
    result: dict[str, Any],
    target_date,
) -> list[tuple[str, str]]:
    """Récupère uniquement les séances explicitement autonomes et identifiées."""
    target_day = target_date.strftime("%Y%m%d")
    found: list[tuple[str, str]] = []

    # Le format texte COROS distingue explicitement les séances autonomes
    # ("Standalone workout") des séances rattachées à un plan ("Plan ID").
    # En l'absence de marqueur explicite, on échoue volontairement fermé :
    # un idInPlan de plan ne doit jamais être envoyé à updateScheduledWorkout.
    for item in result.get("content", []):
        if isinstance(item, str):
            raw_text = item
        elif isinstance(item, dict) and item.get("type") == "text":
            raw_text = item.get("text")
        else:
            continue
        if not isinstance(raw_text, str):
            continue

        # COROS MCP can return a JSON-encoded string inside a string item.
        try:
            decoded_text = json.loads(raw_text)
        except ValueError:
            decoded_text = None
        if isinstance(decoded_text, str):
            raw_text = decoded_text

        current_date = None
        current_name = None
        is_standalone = False
        for raw_line in raw_text.splitlines():
            line = raw_line.strip()
            date_match = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", line)
            if date_match:
                current_date = "".join(date_match.groups())
                current_name = None
                is_standalone = False
                continue
            if not line:
                continue
            if line.casefold().startswith("standalone workout"):
                is_standalone = True
                continue
            if line.startswith("Plan ID:"):
                is_standalone = False
                continue
            id_match = re.fullmatch(r"idInPlan\s*:\s*(\d+)", line, re.IGNORECASE)
            if id_match:
                if (
                    current_date == target_day
                    and is_standalone
                    and current_name
                ):
                    record = (id_match.group(1), current_name)
                    if record not in found:
                        found.append(record)
                current_name = None
                is_standalone = False
                continue
            if (
                current_date is not None
                and current_name is None
                and not line.startswith((
                    "=", "-", "Distance:", "Estimated Time:", "Load:",
                    "To view", "Use Plan ID",
                ))
            ):
                current_name = line

    return found

def _extract_other_coros_workouts(
    result: dict[str, Any],
    *,
    created_id: str | None,
    current_name: str,
) -> list[str]:
    """Retourne les autres séances du jour éventuellement incluses dans le résultat."""
    candidates: list[Any] = []
    structured = result.get("structuredContent")
    if structured is not None:
        candidates.append(structured)
    for item in result.get("content", []):
        if not isinstance(item, dict) or item.get("type") != "text":
            continue
        raw_text = item.get("text")
        if not isinstance(raw_text, str):
            continue
        try:
            candidates.append(json.loads(raw_text))
        except ValueError:
            continue

    found: list[str] = []
    current_normalized = current_name.strip().casefold()
    for candidate in candidates:
        for workout_id, name in _collect_coros_workout_names(candidate):
            if created_id is not None and workout_id == created_id:
                continue
            if name.strip().casefold() == current_normalized:
                continue
            if name not in found:
                found.append(name)
    return found


def _collect_coros_workout_names(value: Any) -> list[tuple[str | None, str]]:
    collected: list[tuple[str | None, str]] = []
    if isinstance(value, dict):
        workout_id = value.get("idInPlan", value.get("id_in_plan"))
        name = (
            value.get("courseName")
            or value.get("workoutName")
            or value.get("name")
            or value.get("title")
        )
        if isinstance(name, str) and name.strip():
            collected.append(
                (str(workout_id) if workout_id is not None else None, name.strip())
            )
        for item in value.values():
            collected.extend(_collect_coros_workout_names(item))
    elif isinstance(value, list):
        for item in value:
            collected.extend(_collect_coros_workout_names(item))
    return collected


def _find_coros_id(value: Any) -> str | None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"idInPlan", "id_in_plan"} and item is not None:
                return str(item)
            found = _find_coros_id(item)
            if found:
                return found
    elif isinstance(value, list):
        for item in value:
            found = _find_coros_id(item)
            if found:
                return found
    return None
