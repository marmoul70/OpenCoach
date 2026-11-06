"""Conversion des prescriptions OpenCoach vers les séances planifiées COROS."""

from __future__ import annotations

import json
import math
import unicodedata
from dataclasses import dataclass
from hashlib import sha256
from typing import Any

from opencoach.models import TrainingSession


class CorosWorkoutMappingError(ValueError):
    """La séance ne peut pas être représentée fidèlement dans COROS."""


@dataclass(frozen=True, slots=True)
class CorosScheduledWorkoutPayload:
    """Payload stable pour createScheduledWorkout."""

    date: str
    course: dict[str, Any]
    payload_hash: str

    def as_tool_arguments(self) -> dict[str, Any]:
        return {"date": self.date, "course": self.course}


def map_training_session_to_coros(
    session: TrainingSession,
) -> CorosScheduledWorkoutPayload:
    """Convertit une séance planifiée sans inventer de prescription."""

    if session.id is None:
        raise CorosWorkoutMappingError(
            "La séance doit être enregistrée dans OpenCoach avant son envoi."
        )
    if session.status != "planned":
        raise CorosWorkoutMappingError(
            "Seules les séances planifiées peuvent être envoyées à COROS."
        )

    requested_sport_type = _map_sport_type(session.sport_type)
    prescription = session.prescription
    if not isinstance(prescription, dict):
        raise CorosWorkoutMappingError(
            "Cette séance ne possède pas de prescription structurée. "
            "Seules les séances générées avec une prescription compatible "
            "peuvent être envoyées."
        )

    work_structure = prescription.get("work_structure")
    if not isinstance(work_structure, dict):
        raise CorosWorkoutMappingError(
            "La prescription ne contient pas de structure de travail exploitable."
        )

    structure_type = str(work_structure.get("type") or "").strip().lower()
    sections: list[dict[str, Any]] = []
    warmup_blocks = _matching_blocks(prescription, "warmup")
    main_blocks = _matching_blocks(prescription, "main")
    easy_blocks = _matching_blocks(prescription, "easy")
    recovery_blocks = _matching_blocks(prescription, "recovery")
    cooldown_blocks = _matching_blocks(prescription, "cooldown")
    sport_type, trail_mode_fallback = _resolve_sport_type(
        requested_sport_type=requested_sport_type,
        session=session,
        work_structure=work_structure,
        main_blocks=main_blocks,
        phase_blocks=(
            *warmup_blocks,
            *easy_blocks,
            *cooldown_blocks,
        ),
    )

    for block in warmup_blocks:
        sections.append(
            _build_phase_section(
                block,
                section_type=1,
                sport_type=sport_type,
                phase_label="échauffement",
            )
        )

    if structure_type == "continuous":
        sections.append(
            _build_continuous_section(
                session=session,
                work_structure=work_structure,
                prescription=prescription,
                sport_type=sport_type,
                warmup_seconds=sum(
                    _block_seconds(block) for block in warmup_blocks
                ),
                cooldown_seconds=sum(
                    _block_seconds(block) for block in cooldown_blocks
                ),
                main_seconds=(
                    _block_seconds(main_blocks[0])
                    if main_blocks and main_blocks[0].get("duration_minutes") is not None
                    else None
                ),
                main_block=main_blocks[0] if main_blocks else None,
            )
        )
    elif structure_type in {"repeats", "intervals"}:
        sections.extend(
            _build_interval_groups(
                work_structure=work_structure,
                prescription=prescription,
                sport_type=sport_type,
                main_block=main_blocks[0] if main_blocks else None,
                recovery_block=(
                    recovery_blocks[0]
                    if recovery_blocks
                    else easy_blocks[0] if easy_blocks else None
                ),
            )
        )
    else:
        raise CorosWorkoutMappingError(
            "Cette structure (renforcement, circuit ou travail technique) "
            "n'est pas encore prise en charge par l'envoi COROS."
        )

    # Les compléments faciles sont des phases réelles de la séance :
    # ils ne doivent pas disparaître entre le travail principal et le cooldown.
    for block in easy_blocks:
        sections.append(
            _build_phase_section(
                block,
                section_type=2,
                sport_type=sport_type,
                phase_label="complément facile",
            )
        )

    for block in cooldown_blocks:
        sections.append(
            _build_phase_section(
                block,
                section_type=4,
                sport_type=sport_type,
                phase_label="retour au calme",
            )
        )

    if not sections:
        raise CorosWorkoutMappingError(
            "La séance ne contient aucune phase compatible avec COROS."
        )

    description = _build_course_description(
        session=session,
        prescription=prescription,
        work_structure=work_structure,
        sport_type=sport_type,
    )
    if trail_mode_fallback:
        trail_note = (
            "Séance configurée comme course à pied pour conserver les étapes "
            "chronométrées ; sur la montre, démarre-la en mode Trail Run."
        )
        if len(description) + 1 + len(trail_note) > 1000:
            raise CorosWorkoutMappingError(
                "Les consignes de la séance et l'instruction de démarrage Trail "
                "dépassent la limite de 1000 caractères de COROS. "
                "Réduis les consignes avant l'envoi."
            )
        description = description.rstrip() + " " + trail_note
    course_name = session.title.strip()
    if not course_name:
        raise CorosWorkoutMappingError(
            "Le nom de la séance ne peut pas être vide."
        )
    course = {
        "sportType": sport_type,
        "courseName": course_name[:100],
        "courseDescription": description,
        "sections": sections,
    }
    arguments = {
        "date": session.date.strftime("%Y%m%d"),
        "course": course,
    }
    serialized = json.dumps(
        arguments,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return CorosScheduledWorkoutPayload(
        date=arguments["date"],
        course=course,
        payload_hash=sha256(serialized.encode("utf-8")).hexdigest(),
    )


def _map_sport_type(value: str) -> int:
    normalized = value.strip().lower().replace("_", "").replace(" ", "")
    mapping = {
        "run": 1,
        "running": 1,
        "trailrun": 5,
        "trailrunning": 5,
        "ride": 2,
        "cycling": 2,
        "bike": 2,
    }
    sport_type = mapping.get(normalized)
    if sport_type is None:
        raise CorosWorkoutMappingError(
            "COROS MCP permet actuellement de créer des séances de course, "
            "trail et vélo. Le renforcement, la natation et les autres sports "
            "ne peuvent pas être envoyés par cette fonction."
        )
    return sport_type


def _resolve_sport_type(
    *,
    requested_sport_type: int,
    session: TrainingSession,
    work_structure: dict[str, Any],
    main_blocks: list[dict[str, Any]],
    phase_blocks: tuple[dict[str, Any], ...],
) -> tuple[int, bool]:
    """Choisit Trail uniquement si toutes les étapes ont une cible Trail.

    COROS autorise l'exécution d'un entraînement de course à pied en mode
    Trail Run sur la montre. Ce mode conserve les cibles chronométrées que
    le type Trail du calendrier ne sait pas représenter. Le type Trail n'est
    retenu que lorsque chaque phase dispose d'une cible distance ou D+.
    """
    if requested_sport_type != 5:
        return requested_sport_type, False

    if any(
        block.get("target_distance_meters") is None
        and block.get("target_elevation_gain_meters") is None
        for block in phase_blocks
    ):
        return 1, True

    structure_type = str(work_structure.get("type") or "").strip().lower()
    if structure_type == "continuous":
        main_block = main_blocks[0] if main_blocks else {}
        has_main_target = any(
            value is not None
            for value in (
                work_structure.get("work_distance_meters"),
                main_block.get("target_distance_meters"),
                main_block.get("target_elevation_gain_meters"),
                session.distance_km,
                session.elevation_gain_m,
            )
        )
        return (5, False) if has_main_target else (1, True)

    if structure_type in {"repeats", "intervals"}:
        intervals = work_structure.get("intervals")
        if not isinstance(intervals, list) or not intervals:
            return 1, True
        for interval in intervals:
            if not isinstance(interval, dict):
                return 1, True
            if (
                interval.get("work_distance_meters") is None
                and interval.get("work_elevation_gain_meters") is None
            ):
                return 1, True
            has_recovery = any(
                interval.get(key) is not None
                for key in (
                    "recovery_duration",
                    "recovery_distance_meters",
                    "recovery_elevation_gain_meters",
                )
            )
            if has_recovery and (
                interval.get("recovery_distance_meters") is None
                and interval.get("recovery_elevation_gain_meters") is None
            ):
                return 1, True
        return 5, False

    return 1, True


def _matching_blocks(
    prescription: dict[str, Any],
    phase: str,
) -> list[dict[str, Any]]:
    blocks = prescription.get("blocks")
    if not isinstance(blocks, list):
        return []
    matches: list[dict[str, Any]] = []
    for block in blocks:
        if not isinstance(block, dict):
            continue
        explicit_phase = str(block.get("phase") or "").strip().lower()
        if explicit_phase:
            if explicit_phase == phase:
                matches.append(block)
            continue
        name = _normalize_text(
            str(block.get("name") or block.get("type") or block.get("label") or "")
        )
        if phase == "warmup" and (
            "warmup" in name or "echauffement" in name or "mise en route" in name
        ):
            matches.append(block)
        elif phase == "cooldown" and (
            "cooldown" in name or "retour au calme" in name or "recuperation finale" in name
        ):
            matches.append(block)
        elif phase == "easy" and (
            "complement facile" in name or "footing facile" in name
        ):
            matches.append(block)
    return matches


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.lower())
    return "".join(character for character in normalized if not unicodedata.combining(character))


def _block_seconds(block: dict[str, Any]) -> int:
    value = block.get("duration_minutes")
    if value is None:
        return 0
    try:
        minutes = float(value)
    except (TypeError, ValueError) as exc:
        raise CorosWorkoutMappingError(
            "Une durée de phase est invalide dans la prescription."
        ) from exc
    if not math.isfinite(minutes) or minutes <= 0:
        raise CorosWorkoutMappingError(
            "Les durées des phases doivent être positives et finies."
        )
    return round(minutes * 60)


def _build_phase_section(
    block: dict[str, Any],
    *,
    section_type: int,
    sport_type: int,
    phase_label: str,
) -> dict[str, Any]:
    distance = block.get("target_distance_meters")
    elevation = block.get("target_elevation_gain_meters")
    explicit_seconds = block.get("target_duration_seconds")

    if sport_type == 5:
        if distance is not None:
            target_type = 1
            target_value = _positive_integer(distance, "distance de phase")
        elif elevation is not None:
            target_type = 3
            target_value = _positive_integer(elevation, "dénivelé de phase")
        else:
            raise CorosWorkoutMappingError(
                f"COROS exige une cible en distance ou en dénivelé pour le {phase_label}. "
                "La prescription ne fournit pas de cible trail convertible."
            )
    elif distance is not None:
        target_type = 1
        target_value = _positive_integer(distance, "distance de phase")
    else:
        seconds = (
            _positive_integer(explicit_seconds, "durée de phase")
            if explicit_seconds is not None
            else _block_seconds(block)
        )
        if seconds <= 0:
            raise CorosWorkoutMappingError(
                f"La durée de {phase_label} est absente ou invalide."
            )
        target_type = 2
        target_value = seconds

    section = {
        "sectionType": section_type,
        "targetType": target_type,
        "targetValue": target_value,
    }
    block_intensity = block.get("intensity")
    if isinstance(block_intensity, dict):
        section.update(_intensity_fields(
            {"intensity": block_intensity},
            sport_type,
        ))
    return section


def _build_continuous_section(
    *,
    session: TrainingSession,
    work_structure: dict[str, Any],
    prescription: dict[str, Any],
    sport_type: int,
    warmup_seconds: int,
    cooldown_seconds: int,
    main_seconds: int | None = None,
    main_block: dict[str, Any] | None = None,
) -> dict[str, Any]:
    distance = work_structure.get("work_distance_meters")
    if distance is None and isinstance(main_block, dict):
        distance = main_block.get("target_distance_meters")
    if distance is None and session.distance_km is not None:
        distance = _positive_integer(
            session.distance_km * 1000,
            "distance",
        )

    if distance is not None:
        section = {
            "sectionType": 2,
            "targetType": 1,
            "targetValue": _positive_integer(distance, "distance"),
        }
    elif sport_type == 5 and (
        (isinstance(main_block, dict) and main_block.get("target_elevation_gain_meters") is not None)
        or session.elevation_gain_m is not None
    ):
        elevation = (
            main_block.get("target_elevation_gain_meters")
            if isinstance(main_block, dict)
            else None
        )
        if elevation is None:
            elevation = session.elevation_gain_m
        section = {
            "sectionType": 2,
            "targetType": 3,
            "targetValue": _positive_integer(elevation, "dénivelé"),
        }
    elif sport_type == 5:
        raise CorosWorkoutMappingError(
            "COROS exige une cible en distance ou en dénivelé pour le trail. "
            "Cette séance ne contient qu'une durée."
        )
    else:
        minutes = (
            round(main_seconds / 60)
            if main_seconds is not None
            else (
                work_structure.get("continuous_minutes")
                or work_structure.get("available_minutes")
            )
        )
        if minutes is None:
            minutes = (
                session.duration_minutes
                - round(warmup_seconds / 60)
                - round(cooldown_seconds / 60)
            )
        duration_minutes = _positive_integer(
            minutes,
            "durée du bloc principal",
        )
        seconds = duration_minutes * 60
        if seconds <= 0:
            raise CorosWorkoutMappingError(
                "La durée du bloc principal est invalide."
            )
        section = {
            "sectionType": 2,
            "targetType": 2,
            "targetValue": seconds,
        }

    block_intensity = (
        main_block.get("intensity")
        if isinstance(main_block, dict)
        else None
    )
    intensity_source = _select_intensity_source(
        block_intensity,
        prescription,
        sport_type,
    )
    section.update(_intensity_fields(intensity_source, sport_type))
    return section


def _build_interval_groups(
    *,
    work_structure: dict[str, Any],
    prescription: dict[str, Any],
    sport_type: int,
    main_block: dict[str, Any] | None = None,
    recovery_block: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Convertit les séries en respectant les récupérations entre répétitions."""
    intervals = work_structure.get("intervals")
    if not isinstance(intervals, list) or not intervals:
        raise CorosWorkoutMappingError(
            "La structure fractionnée ne contient aucun intervalle."
        )

    block_intensity = (
        main_block.get("intensity")
        if isinstance(main_block, dict)
        else None
    )
    intensity_source = _select_intensity_source(
        block_intensity,
        prescription,
        sport_type,
    )
    sections: list[dict[str, Any]] = []
    for interval in intervals:
        if not isinstance(interval, dict):
            raise CorosWorkoutMappingError(
                "Un intervalle de la prescription est invalide."
            )
        repetitions = _positive_integer(
            interval.get("repetitions"),
            "nombre de répétitions",
        )
        work_section = _build_work_section(
            interval=interval,
            prescription=intensity_source,
            sport_type=sport_type,
        )
        recovery_duration = interval.get("recovery_duration")
        recovery_distance = interval.get("recovery_distance_meters")
        recovery_elevation = interval.get("recovery_elevation_gain_meters")
        has_recovery = any(
            value is not None
            for value in (recovery_duration, recovery_distance, recovery_elevation)
        )

        if not has_recovery or repetitions == 1:
            remaining = repetitions
            while remaining > 0:
                chunk = min(remaining, 20)
                if chunk == 1:
                    sections.append(work_section)
                else:
                    sections.append({
                        "intervalGroup": True,
                        "repeats": chunk,
                        "sets": [work_section],
                    })
                remaining -= chunk
            continue

        if sport_type == 5:
            if recovery_distance is not None:
                recovery_section = {
                    "sectionType": 3,
                    "targetType": 1,
                    "targetValue": _positive_integer(
                        recovery_distance,
                        "distance de récupération",
                    ),
                }
            elif recovery_elevation is not None:
                recovery_section = {
                    "sectionType": 3,
                    "targetType": 3,
                    "targetValue": _positive_integer(
                        recovery_elevation,
                        "dénivelé de récupération",
                    ),
                }
            else:
                raise CorosWorkoutMappingError(
                    "COROS n'accepte pas de récupération chronométrée "
                    "dans un entraînement trail. Fournis une distance ou "
                    "un dénivelé explicite pour cette récupération."
                )
        elif recovery_distance is not None:
            recovery_section = {
                "sectionType": 3,
                "targetType": 1,
                "targetValue": _positive_integer(
                    recovery_distance,
                    "distance de récupération",
                ),
            }
        elif recovery_duration is not None:
            recovery_seconds = _duration_seconds(
                recovery_duration,
                interval.get("recovery_unit"),
                default_unit="seconds",
            )
            recovery_section = {
                "sectionType": 3,
                "targetType": 2,
                "targetValue": recovery_seconds,
            }
        else:
            raise CorosWorkoutMappingError(
                "Une récupération en dénivelé n'est disponible que pour le trail."
            )

        # Une phase recovery explicitement prescrite est prioritaire.
        # Si elle n'offre qu'une cible non pilotable (ex. RPE), on conserve
        # le fallback global historique lorsqu'il est compatible COROS.
        fallback_recovery_intensity = prescription.get("recovery_intensity")
        fallback_recovery = (
            {"intensity": fallback_recovery_intensity}
            if isinstance(fallback_recovery_intensity, dict)
            else {}
        )
        recovery_intensity_source = _select_intensity_source(
            (
                recovery_block.get("intensity")
                if isinstance(recovery_block, dict)
                else None
            ),
            fallback_recovery,
            sport_type,
        )
        if isinstance(recovery_intensity_source.get("intensity"), dict):
            recovery_section.update(
                _intensity_fields(recovery_intensity_source, sport_type)
            )

        # Chaque groupe COROS est limité à 20 répétitions. Le découpage
        # conserve exactement les répétitions et les récupérations inter-reps,
        # sans ajouter de récupération après la dernière répétition.
        remaining = repetitions
        while remaining > 0:
            chunk = min(remaining, 20)
            if chunk == 1:
                sections.append(work_section)
            else:
                sections.append({
                    "intervalGroup": True,
                    "repeats": chunk - 1,
                    "sets": [work_section, recovery_section],
                })
                sections.append(work_section)
            remaining -= chunk
            if remaining > 0:
                sections.append(recovery_section)

    return sections


def _build_work_section(
    *,
    interval: dict[str, Any],
    prescription: dict[str, Any],
    sport_type: int,
) -> dict[str, Any]:
    distance = interval.get("work_distance_meters")
    elevation = interval.get("work_elevation_gain_meters")
    duration = interval.get("work_duration")
    unit = interval.get("work_unit")

    if distance is not None:
        section = {
            "sectionType": 2,
            "targetType": 1,
            "targetValue": _positive_integer(distance, "distance de répétition"),
        }
    elif elevation is not None and sport_type == 5:
        section = {
            "sectionType": 2,
            "targetType": 3,
            "targetValue": _positive_integer(elevation, "dénivelé de répétition"),
        }
    elif duration is not None:
        if sport_type == 5:
            raise CorosWorkoutMappingError(
                "COROS exige une cible en distance ou en dénivelé pour les fractions trail."
            )
        section = {
            "sectionType": 2,
            "targetType": 2,
            "targetValue": _duration_seconds(
                duration,
                unit,
                default_unit="minutes",
            ),
        }
    else:
        raise CorosWorkoutMappingError(
            "Une répétition doit avoir une durée ou une distance."
        )

    repetition_target = interval.get("repetition_target")
    repetition_intensity = (
        _pace_fields_from_repetition_target(repetition_target)
        if sport_type != 2
        else None
    )
    if repetition_intensity is not None:
        section.update(repetition_intensity)
    else:
        section.update(_intensity_fields(prescription, sport_type))
    return section


def _select_intensity_source(
    block_intensity: Any,
    fallback_prescription: dict[str, Any],
    sport_type: int,
) -> dict[str, Any]:
    """Privilégie la cible du bloc, avec repli sur la prescription principale.

    Un bloc peut conserver un RPE historique alors que la prescription globale
    a depuis été enrichie avec une cible COROS-compatible (FC ou allure VMA).
    Le repli ne s'applique qu'au travail principal, jamais aux phases faciles.
    """
    if isinstance(block_intensity, dict):
        candidate = {"intensity": block_intensity}
        try:
            _intensity_fields(candidate, sport_type)
        except CorosWorkoutMappingError:
            return fallback_prescription
        return candidate
    return fallback_prescription


def _intensity_fields(
    prescription: dict[str, Any],
    sport_type: int,
) -> dict[str, int]:
    intensity = prescription.get("intensity")
    targets = intensity.get("targets") if isinstance(intensity, dict) else None
    if not isinstance(targets, list):
        raise CorosWorkoutMappingError(
            "La séance ne possède pas de cible physiologique compatible avec COROS."
        )

    for target in targets:
        if not isinstance(target, dict):
            continue
        reference = str(target.get("reference") or "").strip().lower()
        # COROS attend une fréquence cardiaque absolue en bpm.
        # La réserve de FC (HRR) est un pourcentage/réserve et ne
        # doit jamais être transmise comme une valeur bpm.
        if reference == "heart_rate":
            minimum = _bounded_integer(
                target.get("minimum"), 30, 240, "fréquence cardiaque minimale"
            )
            maximum = _bounded_integer(
                target.get("maximum"), 30, 240, "fréquence cardiaque maximale"
            )
            if maximum < minimum:
                raise CorosWorkoutMappingError(
                    "La plage de fréquence cardiaque est incohérente."
                )
            return {
                "intensityType": 1,
                "intensityValueStart": minimum,
                "intensityValueEnd": maximum,
            }
        if reference == "vma_percent" and sport_type in {1, 5}:
            derived = target.get("derived")
            pace = (
                derived.get("pace_seconds_per_km")
                if isinstance(derived, dict)
                else None
            )
            if not isinstance(pace, dict):
                continue
            fastest = _bounded_integer(
                pace.get("fastest"), 120, 1499, "allure minimale"
            )
            slowest = _bounded_integer(
                pace.get("slowest"), 120, 1499, "allure maximale"
            )
            if slowest < fastest:
                raise CorosWorkoutMappingError(
                    "La plage d'allure issue de la VMA est incohérente."
                )
            return {
                "intensityType": 2,
                "intensityValueStart": fastest,
                "intensityValueEnd": slowest,
            }

    raise CorosWorkoutMappingError(
        "La prescription est uniquement exprimée en RPE ou dans une unité "
        "que COROS ne sait pas piloter. Il faut une cible de fréquence "
        "cardiaque (bpm) ou, en course/trail, une allure calculée."
    )


def _pace_fields_from_repetition_target(
    target: Any,
) -> dict[str, int] | None:
    if not isinstance(target, dict):
        return None
    try:
        distance = float(target.get("distance_meters"))
        fast_seconds = float(target.get("fast_seconds"))
        slow_seconds = float(target.get("slow_seconds"))
    except (TypeError, ValueError):
        return None
    if (
        not all(math.isfinite(value) for value in (
            distance,
            fast_seconds,
            slow_seconds,
        ))
        or distance <= 0
        or fast_seconds <= 0
        or slow_seconds <= 0
    ):
        return None

    fastest = round(fast_seconds * 1000 / distance)
    slowest = round(slow_seconds * 1000 / distance)
    if not (120 <= fastest <= 1499 and 120 <= slowest <= 1499):
        return None
    return {
        "intensityType": 2,
        "intensityValueStart": min(fastest, slowest),
        "intensityValueEnd": max(fastest, slowest),
    }


def _duration_seconds(
    value: Any,
    unit: Any,
    *,
    default_unit: str,
) -> int:
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise CorosWorkoutMappingError(
            "Une durée d'intervalle est invalide."
        ) from exc
    if not math.isfinite(numeric) or numeric <= 0:
        raise CorosWorkoutMappingError(
            "Les durées des intervalles doivent être positives et finies."
        )
    normalized = str(unit or default_unit).strip().lower()
    if normalized in {"second", "seconds", "sec", "s"}:
        seconds = round(numeric)
    elif normalized in {"minute", "minutes", "min", "m"}:
        seconds = round(numeric * 60)
    else:
        raise CorosWorkoutMappingError(
            "L'unité de durée de l'intervalle n'est pas reconnue."
        )
    if seconds <= 0:
        raise CorosWorkoutMappingError(
            "Les durées des intervalles doivent être positives et finies."
        )
    return seconds


def _positive_integer(value: Any, label: str) -> int:
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise CorosWorkoutMappingError(
            f"La {label} est invalide."
        ) from exc
    if not math.isfinite(numeric):
        raise CorosWorkoutMappingError(
            f"La {label} doit être une valeur finie."
        )
    result = round(numeric)
    if result <= 0 or abs(numeric - result) > 1e-6:
        raise CorosWorkoutMappingError(
            f"La {label} doit être un entier strictement positif."
        )
    return result


def _bounded_integer(
    value: Any,
    minimum: int,
    maximum: int,
    label: str,
) -> int:
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise CorosWorkoutMappingError(
            f"La {label} est invalide."
        ) from exc
    if not math.isfinite(numeric):
        raise CorosWorkoutMappingError(
            f"La {label} doit être une valeur finie."
        )
    result = round(numeric)
    if not minimum <= result <= maximum:
        raise CorosWorkoutMappingError(
            f"{label.capitalize()} doit être comprise entre {minimum} et {maximum}."
        )
    return result


def _build_course_description(
    *,
    session: TrainingSession,
    prescription: dict[str, Any],
    work_structure: dict[str, Any],
    sport_type: int,
) -> str:
    session_lines = [
        line.strip()
        for line in (session.description or "").splitlines()
        if line.strip()
    ]
    blocks = prescription.get("blocks")
    block_description_markers = [
        (
            str(block.get("name") or block.get("label") or "").strip().casefold(),
            str(block.get("description") or "").strip().casefold(),
        )
        for block in blocks
        if isinstance(block, dict)
        and str(block.get("name") or block.get("label") or "").strip()
        and str(block.get("description") or "").strip()
    ] if isinstance(blocks, list) else []
    secondary_guidance = [
        line
        for line in session_lines
        if line.casefold().startswith("stimulus complémentaire")
    ]
    regular_description = [
        line
        for line in session_lines
        if not line.casefold().startswith("stimulus complémentaire")
        and not any(
            name in line.casefold() and detail in line.casefold()
            for name, detail in block_description_markers
        )
    ]
    parts = [
        regular_description[0]
        if regular_description
        else session.title.strip()
    ]
    # Les consignes secondaires sont prioritaires dans le champ limité à
    # 1000 caractères de COROS : elles passent avant les détails descriptifs
    # redondants afin de ne pas être coupées en fin de chaîne.
    parts.extend(secondary_guidance)
    if secondary_guidance:
        mandatory_description = " ".join(
            [parts[0], *secondary_guidance]
        )
        if len(mandatory_description) > 999:
            raise CorosWorkoutMappingError(
                "Les consignes secondaires dépassent la capacité de description "
                "COROS. Réduis le nombre de stimuli regroupés avant l'envoi."
            )
    if isinstance(blocks, list):
        for block in blocks:
            if not isinstance(block, dict):
                continue
            name = str(block.get("name") or block.get("label") or "").strip()
            detail = str(block.get("description") or "").strip()
            duration = block.get("duration_minutes")
            target_parts = []
            if duration is not None:
                target_parts.append(f"{duration} min")
            target_seconds = block.get("target_duration_seconds")
            if target_seconds is not None:
                target_parts.append(f"{target_seconds} s")
            distance = block.get("target_distance_meters")
            if distance is not None:
                target_parts.append(f"{distance} m")
            elevation = block.get("target_elevation_gain_meters")
            if elevation is not None:
                target_parts.append(f"{elevation} m D+")
            heading = " — ".join(part for part in (name, ", ".join(target_parts)) if part)
            if heading or detail:
                parts.append(": ".join(part for part in (heading, detail) if part))
            block_intensity = block.get("intensity")
            block_targets = (
                block_intensity.get("targets")
                if isinstance(block_intensity, dict)
                else None
            )
            if isinstance(block_targets, list):
                for target in block_targets:
                    if not isinstance(target, dict):
                        continue
                    reference = str(target.get("reference") or "").strip().lower()
                    # Les cibles cardiaques et les allures VMA pilotables sont
                    # déjà présentes dans les étapes COROS : ne pas les dupliquer.
                    if reference in {"heart_rate", "vma_percent"}:
                        continue
                    label = target.get("label") or reference or "Intensité"
                    minimum = target.get("minimum")
                    maximum = target.get("maximum")
                    unit = target.get("unit") or ""
                    if minimum is not None and maximum is not None:
                        parts.append(
                            f"{name or 'Phase'} : {label} {minimum}–{maximum} {unit}".strip()
                        )
    recovery_intensity = prescription.get("recovery_intensity")
    recovery_targets = (
        recovery_intensity.get("targets")
        if isinstance(recovery_intensity, dict)
        else None
    )
    if isinstance(recovery_targets, list):
        for target in recovery_targets:
            if not isinstance(target, dict):
                continue
            reference = str(target.get("reference") or "").strip().lower()
            if reference in {"heart_rate", "vma_percent"}:
                continue
            label = target.get("label") or reference or "Intensité"
            minimum = target.get("minimum")
            maximum = target.get("maximum")
            unit = target.get("unit") or ""
            if minimum is not None and maximum is not None:
                parts.append(
                    f"Récupérations : {label} {minimum}–{maximum} {unit}."
                )

    intervals = work_structure.get("intervals")
    has_repetition_pace = (
        sport_type != 2
        and isinstance(intervals, list)
        and any(
            isinstance(interval, dict)
            and isinstance(interval.get("repetition_target"), dict)
            for interval in intervals
        )
    )
    if has_repetition_pace:
        parts.append(
            "Allure des répétitions pilotée par les temps de passage "
            "calculés dans la prescription."
        )
        for index, interval in enumerate(intervals, start=1):
            if not isinstance(interval, dict):
                continue
            target = interval.get("repetition_target")
            if not isinstance(target, dict):
                continue
            try:
                distance = float(target.get("distance_meters"))
                fast_seconds = float(target.get("fast_seconds"))
                slow_seconds = float(target.get("slow_seconds"))
                vma_min = float(target.get("vma_percent_min"))
                vma_max = float(target.get("vma_percent_max"))
            except (TypeError, ValueError):
                continue
            if (
                not all(math.isfinite(value) for value in (
                    distance, fast_seconds, slow_seconds, vma_min, vma_max
                ))
                or distance <= 0
                or fast_seconds <= 0
                or slow_seconds <= 0
            ):
                continue
            fastest_pace = fast_seconds * 1000 / distance
            slowest_pace = slow_seconds * 1000 / distance
            parts.append(
                f"Série {index} : {distance:g} m en "
                f"{_format_elapsed(fast_seconds)}–{_format_elapsed(slow_seconds)}, "
                f"soit {_format_pace(fastest_pace)}–"
                f"{_format_pace(slowest_pace)}/km à "
                f"{vma_min:g}–{vma_max:g} % VMA."
            )

    if isinstance(intervals, list):
        for index, interval in enumerate(intervals, start=1):
            if not isinstance(interval, dict):
                continue
            work_elevation = interval.get("work_elevation_gain_meters")
            work_duration = interval.get("work_duration")
            work_unit = str(interval.get("work_unit") or "minutes")
            recovery_elevation = interval.get("recovery_elevation_gain_meters")
            recovery_duration = interval.get("recovery_duration")
            recovery_unit = str(interval.get("recovery_unit") or "seconds")
            if work_elevation is not None:
                parts.append(f"Série {index} : {work_elevation} m D+.")
            if work_duration is not None:
                parts.append(f"Série {index} : {work_duration} {work_unit}.")
            if recovery_elevation is not None:
                parts.append(f"Récupération série {index} : {recovery_elevation} m D+.")
            if recovery_duration is not None:
                parts.append(f"Récupération série {index} : {recovery_duration} {recovery_unit}.")

    description = " ".join(part for part in parts if part)
    if len(description) > 1000:
        raise CorosWorkoutMappingError(
            "Les consignes complètes de la séance dépassent la limite de "
            "1000 caractères de COROS. Aucune consigne ne sera coupée : "
            "réduis ou regroupe les descriptions avant l'envoi."
        )
    return description or "Séance planifiée par OpenCoach."


def _format_elapsed(value: Any) -> str:
    try:
        seconds = round(float(value))
    except (TypeError, ValueError):
        return "—"
    minutes, remainder = divmod(seconds, 60)
    return f"{minutes}:{remainder:02d}"


def _format_pace(value: Any) -> str:
    try:
        seconds = round(float(value))
    except (TypeError, ValueError):
        return "—"
    minutes, remainder = divmod(seconds, 60)
    return f"{minutes}:{remainder:02d}"
