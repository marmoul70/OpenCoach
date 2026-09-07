"""Mapping des séances OpenCoach vers les workouts Intervals.icu.

Ce module ne réalise aucun appel réseau.

Il transforme une TrainingSession persistée en représentation stable
pouvant ensuite être envoyée au calendrier Intervals.icu.

L'identifiant externe dépend uniquement de l'identité OpenCoach de la
séance. Une adaptation conserve donc le même external_id et pourra être
envoyée en upsert sans créer de doublon.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import re
from typing import Any

from opencoach.coaching.session_guidance import (
    build_session_guidance,
)
from opencoach.models import TrainingSession


@dataclass(frozen=True, slots=True)
class IntervalsWorkoutPayload:
    """Workout planifié destiné à Intervals.icu."""

    external_id: str
    category: str
    start_date_local: str
    type: str
    name: str
    description: str

    def as_dict(self) -> dict[str, str]:
        """Retourne le payload JSON stable destiné à l'API."""
        return {
            "external_id": self.external_id,
            "category": self.category,
            "start_date_local": self.start_date_local,
            "type": self.type,
            "name": self.name,
            "description": self.description,
        }

    def payload_hash(self) -> str:
        """Empreinte stable utilisée pour détecter les modifications."""
        serialized = json.dumps(
            self.as_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )

        return sha256(
            serialized.encode("utf-8")
        ).hexdigest()


def build_intervals_external_id(
    session: TrainingSession,
) -> str:
    """Construit l'identifiant stable OpenCoach côté Intervals."""

    if session.id is None:
        raise ValueError(
            "Une séance doit être persistée avant synchronisation "
            "vers Intervals.icu."
        )

    return f"opencoach:session:{session.id}"



def map_training_session_to_intervals(
    session: TrainingSession,
) -> IntervalsWorkoutPayload | None:
    """Mappe une séance OpenCoach vers Intervals.icu."""

    payload = (
        _map_training_session_to_intervals_base(
            session
        )
    )

    if payload is None:
        return None

    if session.type != "long_endurance":
        return payload

    return IntervalsWorkoutPayload(
        external_id=payload.external_id,
        category=payload.category,
        start_date_local=payload.start_date_local,
        type=payload.type,
        name=payload.name,
        description=(
            _build_long_endurance_description(
                session
            )
        ),
    )


def _build_long_endurance_description(
    session: TrainingSession,
) -> str:
    """Construit les phases exécutables d'une sortie longue."""

    guidance = build_session_guidance(
        session
    )

    lines: list[str] = []

    for step in guidance.warmup:
        if step.duration_minutes is None:
            continue

        lines.extend(
            (
                "Échauffement",
                f"- {step.duration_minutes}m",
                "",
            )
        )

    for step in guidance.main_set:
        if step.duration_minutes is None:
            continue

        lines.extend(
            (
                session.title,
                f"- {step.duration_minutes}m",
            )
        )

    for step in guidance.cooldown:
        if step.duration_minutes is None:
            continue

        lines.extend(
            (
                "",
                "Retour au calme",
                f"- {step.duration_minutes}m",
            )
        )

    return "\n".join(lines)


def _map_training_session_to_intervals_base(


    session: TrainingSession,
) -> IntervalsWorkoutPayload | None:
    """Convertit une séance OpenCoach en workout Intervals.

    Le renforcement n'est volontairement pas synchronisé dans cette
    première version : T6.6 cible les entraînements exécutables sur
    la montre.
    """

    intervals_type = _map_sport_type(
        session.sport_type
    )

    if intervals_type is None:
        return None

    description = _build_workout_description(
        session
    )

    return IntervalsWorkoutPayload(
        external_id=build_intervals_external_id(
            session
        ),
        category="WORKOUT",
        start_date_local=(
            f"{session.date.isoformat()}T00:00:00"
        ),
        type=intervals_type,
        name=session.title,
        description=description,
    )


def _map_sport_type(
    sport_type: str,
) -> str | None:
    normalized = sport_type.strip().lower()

    mapping = {
        "run": "Run",
        "running": "Run",
        "trailrun": "Run",
        "trail_run": "Run",
        "trail running": "Run",
        "ride": "Ride",
        "cycling": "Ride",
        "bike": "Ride",
    }

    return mapping.get(normalized)


def _build_workout_description(
    session: TrainingSession,
) -> str:
    prescription = session.prescription or {}

    work_structure = prescription.get(
        "work_structure"
    )

    if isinstance(work_structure, dict):
        structure_type = work_structure.get(
            "type"
        )

        if structure_type == "continuous":
            return _build_continuous_description(
                session=session,
                prescription=prescription,
                work_structure=work_structure,
            )

        if structure_type == "repeats":
            result = _build_repeats_description(
                session=session,
                prescription=prescription,
                work_structure=work_structure,
            )

            if result is not None:
                return result

    return _build_safe_fallback(session)


def _build_continuous_description(
    *,
    session: TrainingSession,
    prescription: dict[str, Any],
    work_structure: dict[str, Any],
) -> str:
    guidance = build_session_guidance(
        session
    )

    warmup_minutes = sum(
        step.duration_minutes or 0
        for step in guidance.warmup
    )

    cooldown_minutes = sum(
        step.duration_minutes or 0
        for step in guidance.cooldown
    )

    main_minutes = (
        session.duration_minutes
        - warmup_minutes
        - cooldown_minutes
    )

    if main_minutes <= 0:
        main_minutes = int(
            work_structure.get(
                "continuous_minutes"
            )
            or work_structure.get(
                "available_minutes"
            )
            or session.duration_minutes
        )

    target = _primary_target(
        prescription
    )

    target_text = _format_target(
        target
    )

    main_line = (
        f"- {main_minutes}m"
    )

    if target_text:
        main_line += (
            f" {target_text}"
        )

    lines: list[str] = []

    if warmup_minutes > 0:
        lines.extend(
            (
                "Échauffement",
                f"- {warmup_minutes}m",
                "",
            )
        )

    lines.extend(
        (
            session.title,
            main_line,
        )
    )

    if cooldown_minutes > 0:
        lines.extend(
            (
                "",
                "Retour au calme",
                f"- {cooldown_minutes}m",
            )
        )

    return "\n".join(
        lines
    )


def _build_repeats_description(
    *,
    session: TrainingSession,
    prescription: dict[str, Any],
    work_structure: dict[str, Any],
) -> str | None:
    intervals = work_structure.get(
        "intervals"
    )

    if (
        not isinstance(intervals, list)
        or not intervals
    ):
        return None

    lines: list[str] = []

    warmup_minutes = _extract_named_block_minutes(
        prescription,
        "warmup",
    )

    if warmup_minutes:
        lines.extend(
            (
                "Échauffement",
                f"- {warmup_minutes}m",
                "",
            )
        )

    for interval in intervals:
        if not isinstance(interval, dict):
            continue

        repetitions = int(
            interval.get("repetitions") or 1
        )

        lines.append(f"{repetitions}x")

        work_line = _build_work_line(
            interval=interval,
            prescription=prescription,
        )

        if work_line:
            lines.append(work_line)

        recovery_line = _build_recovery_line(
            interval
        )

        if recovery_line:
            lines.append(recovery_line)

        lines.append("")

    cooldown_minutes = _extract_named_block_minutes(
        prescription,
        "cooldown",
    )

    if cooldown_minutes:
        lines.extend(
            (
                "Retour au calme",
                f"- {cooldown_minutes}m",
            )
        )

    result = "\n".join(lines).strip()

    if not result:
        return None

    return result


def _build_work_line(
    *,
    interval: dict[str, Any],
    prescription: dict[str, Any],
) -> str | None:
    distance = (
        interval.get("work_distance_meters")
    )

    duration = interval.get(
        "work_duration"
    )

    unit = interval.get(
        "work_unit"
    )

    repetition_target = interval.get(
        "repetition_target"
    )

    if not isinstance(
        repetition_target,
        dict,
    ):
        repetition_target = {}

    if distance:
        base = f"- {_format_number(distance)}mtr"
    elif duration:
        formatted = _format_duration(
            duration,
            unit,
        )

        if formatted is None:
            return None

        base = f"- {formatted}"
    else:
        return None

    pace = _pace_from_repetition_target(
        repetition_target
    )

    if pace:
        return f"{base} {pace} Pace"

    target = _primary_target(prescription)
    target_text = _format_target(target)

    if target_text:
        return f"{base} {target_text}"

    return base


def _build_recovery_line(
    interval: dict[str, Any],
) -> str | None:
    duration = interval.get(
        "recovery_duration"
    )

    if not duration:
        return None

    formatted = _format_duration(
        duration,
        interval.get("recovery_unit"),
    )

    if formatted is None:
        return None

    return f"- {formatted} recovery"


def _format_duration(
    value: Any,
    unit: Any,
) -> str | None:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None

    normalized = str(
        unit or ""
    ).strip().lower()

    if normalized in {
        "second",
        "seconds",
        "sec",
        "s",
    }:
        return f"{_format_number(numeric)}s"

    if normalized in {
        "minute",
        "minutes",
        "min",
        "m",
    }:
        return f"{_format_number(numeric)}m"

    # Certaines structures historiques stockent les durées
    # sans unité explicite en minutes.
    if not normalized:
        return f"{_format_number(numeric)}m"

    return None


def _pace_from_repetition_target(
    target: dict[str, Any],
) -> str | None:
    fast_seconds = target.get(
        "fast_seconds"
    )
    slow_seconds = target.get(
        "slow_seconds"
    )
    distance = target.get(
        "distance_meters"
    )

    if not distance:
        return None

    try:
        distance_m = float(distance)
    except (TypeError, ValueError):
        return None

    if distance_m <= 0:
        return None

    paces: list[float] = []

    for seconds in (
        fast_seconds,
        slow_seconds,
    ):
        if seconds is None:
            continue

        try:
            seconds_value = float(seconds)
        except (TypeError, ValueError):
            continue

        if seconds_value <= 0:
            continue

        paces.append(
            seconds_value
            * 1000.0
            / distance_m
        )

    if not paces:
        return None

    fastest = min(paces)
    slowest = max(paces)

    if len(paces) == 1:
        return _format_pace(fastest)

    return (
        f"{_format_pace(fastest)}-"
        f"{_format_pace(slowest)}"
    )


def _format_pace(
    seconds_per_km: float,
) -> str:
    total_seconds = int(
        round(seconds_per_km)
    )

    minutes, seconds = divmod(
        total_seconds,
        60,
    )

    return f"{minutes}:{seconds:02d}/km"


def _primary_target(
    prescription: dict[str, Any],
) -> dict[str, Any] | None:
    intensity = prescription.get(
        "intensity"
    )

    if not isinstance(intensity, dict):
        return None

    targets = intensity.get(
        "targets"
    )

    if (
        not isinstance(targets, list)
        or not targets
    ):
        return None

    # La sérialisation OpenCoach conserve normalement l'ordre
    # de priorité de SessionIntensityPrescription.
    for target in targets:
        if isinstance(target, dict):
            return target

    return None


def _format_target(
    target: dict[str, Any] | None,
) -> str | None:
    if target is None:
        return None

    reference = str(
        target.get("reference") or ""
    ).strip().lower()

    minimum = target.get("minimum")
    maximum = target.get("maximum")

    if reference in {
        "heart_rate",
        "hr",
    }:
        if minimum is None or maximum is None:
            return None

        return (
            f"{_format_number(minimum)}-"
            f"{_format_number(maximum)}bpm HR"
        )

    # RPE reste une consigne utile pour l'athlète mais n'est
    # volontairement pas transformé en cible montre.
    if reference == "rpe":
        if minimum is None or maximum is None:
            return None

        return (
            f"RPE {_format_number(minimum)}-"
            f"{_format_number(maximum)}"
        )

    return None


def _extract_named_block_minutes(
    prescription: dict[str, Any],
    name: str,
) -> int | None:
    """Tolère les structures présentes/futures sans les imposer."""

    blocks = prescription.get("blocks")

    if not isinstance(blocks, list):
        return None

    wanted = name.lower()

    for block in blocks:
        if not isinstance(block, dict):
            continue

        block_name = str(
            block.get("type")
            or block.get("name")
            or block.get("label")
            or ""
        ).lower()

        if wanted not in block_name:
            continue

        value = (
            block.get("duration_minutes")
            or block.get("minutes")
        )

        if value is None:
            continue

        try:
            return int(value)
        except (TypeError, ValueError):
            continue

    return None


def _build_safe_fallback(
    session: TrainingSession,
) -> str:
    """Construit un workout continu sans inventer de fractionné."""

    target = _heart_rate_from_legacy_text(
        session.heart_rate_zone
    )

    line = f"- {session.duration_minutes}m"

    if target:
        line += f" {target}"

    lines = [
        session.title,
        line,
    ]

    if session.description:
        lines.extend(
            (
                "",
                session.description,
            )
        )

    return "\n".join(lines)


def _heart_rate_from_legacy_text(
    value: str | None,
) -> str | None:
    if not value:
        return None

    match = re.search(
        r"(\d{2,3})\s*[–-]\s*(\d{2,3})\s*bpm",
        value,
        flags=re.IGNORECASE,
    )

    if match is None:
        return None

    return (
        f"{match.group(1)}-"
        f"{match.group(2)}bpm HR"
    )


def _format_number(
    value: Any,
) -> str:
    numeric = float(value)

    if numeric.is_integer():
        return str(int(numeric))

    return (
        f"{numeric:.2f}"
        .rstrip("0")
        .rstrip(".")
    )
