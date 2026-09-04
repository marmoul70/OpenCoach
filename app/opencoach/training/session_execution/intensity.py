"""Analyse déterministe de l'intensité d'une séance réalisée."""

from __future__ import annotations

from typing import Any

from opencoach.models import (
    Activity,
    ActivityDetail,
    TrainingSession,
)

from .metric import (
    NumericMetricAssessment,
    NumericTarget,
)
from .models import SessionExecutionIntensityAssessment
from .status import AssessmentStatus
from .stream_analysis import calculate_time_in_range
from .thresholds import (
    DEFAULT_TARGET_ADHERENCE_THRESHOLDS,
    TargetAdherenceThresholds,
)


RANGE_PARTIAL_TOLERANCE_PERCENT = 5.0


def assess_session_intensity(
    session: TrainingSession,
    activity: Activity | None,
    activity_detail: ActivityDetail | None = None,
    *,
    adherence_thresholds: TargetAdherenceThresholds = (
        DEFAULT_TARGET_ADHERENCE_THRESHOLDS
    ),
) -> SessionExecutionIntensityAssessment:
    """Compare l'intensité prévue et l'intensité réalisée.

    Les moyennes globales ne sont volontairement pas utilisées
    pour juger l'intensité d'une séance fractionnée.

    Les répétitions et récupérations nécessiteront des laps ou
    streams détaillés dans une étape ultérieure.
    """

    structured_intervals = _has_structured_intervals(
        session,
    )

    heart_rate = _assess_average_heart_rate(
        session,
        activity,
        structured_intervals=structured_intervals,
    )

    average_speed = _assess_average_speed(
        session,
        activity,
        structured_intervals=structured_intervals,
    )

    average_pace = _assess_average_pace(
        session,
        activity,
        structured_intervals=structured_intervals,
    )

    time_in_heart_rate_target = (
        _assess_time_in_heart_rate_target(
            session,
            activity_detail,
            structured_intervals=structured_intervals,
            thresholds=adherence_thresholds,
        )
    )

    time_in_pace_target = (
        _assess_time_in_speed_target(
            session,
            activity_detail,
            structured_intervals=structured_intervals,
            thresholds=adherence_thresholds,
        )
    )

    return SessionExecutionIntensityAssessment(
        average_heart_rate=heart_rate,
        average_speed=average_speed,
        average_pace=average_pace,
        average_vma_percent=None,
        time_in_heart_rate_target=(
            time_in_heart_rate_target
        ),
        time_in_pace_target=time_in_pace_target,
    )


def _assess_average_heart_rate(
    session: TrainingSession,
    activity: Activity | None,
    *,
    structured_intervals: bool,
) -> NumericMetricAssessment:
    target = _find_target(
        session,
        reference="heart_rate",
    )

    if target is None:
        target = _find_target(
            session,
            reference="heart_rate_reserve",
        )

    if target is None:
        return _not_applicable(
            key="average_heart_rate",
            label="Fréquence cardiaque moyenne",
            details=(
                "Aucune cible cardiaque absolue structurée "
                "n'est prescrite pour cette séance."
            ),
        )

    numeric_target = NumericTarget(
        minimum=target["minimum"],
        maximum=target["maximum"],
        unit=target["unit"],
    )

    if structured_intervals:
        return _not_applicable(
            key="average_heart_rate",
            label="Fréquence cardiaque moyenne",
            target=numeric_target,
            details=(
                "La fréquence cardiaque moyenne globale "
                "n'est pas utilisée pour juger une séance "
                "fractionnée."
            ),
        )

    if activity is None:
        return _insufficient(
            key="average_heart_rate",
            label="Fréquence cardiaque moyenne",
            target=numeric_target,
            details="Aucune activité associée à la séance.",
        )

    if activity.average_heart_rate is None:
        return _insufficient(
            key="average_heart_rate",
            label="Fréquence cardiaque moyenne",
            target=numeric_target,
            details=(
                "La fréquence cardiaque moyenne "
                "n'est pas disponible."
            ),
        )

    return _compare_range(
        key="average_heart_rate",
        label="Fréquence cardiaque moyenne",
        target=numeric_target,
        actual=float(
            activity.average_heart_rate
        ),
    )


def _assess_average_speed(
    session: TrainingSession,
    activity: Activity | None,
    *,
    structured_intervals: bool,
) -> NumericMetricAssessment:
    target = _find_vma_target(
        session,
    )

    speed_target = _derived_speed_target(
        target,
    )

    if speed_target is None:
        return _not_applicable(
            key="average_speed",
            label="Vitesse moyenne",
            details=(
                "Aucune cible de vitesse structurée "
                "n'est disponible pour cette séance."
            ),
        )

    if structured_intervals:
        return _not_applicable(
            key="average_speed",
            label="Vitesse moyenne",
            target=speed_target,
            details=(
                "La vitesse moyenne globale n'est pas "
                "utilisée pour juger une séance fractionnée."
            ),
        )

    if activity is None:
        return _insufficient(
            key="average_speed",
            label="Vitesse moyenne",
            target=speed_target,
            details="Aucune activité associée à la séance.",
        )

    if activity.average_speed_mps is None:
        return _insufficient(
            key="average_speed",
            label="Vitesse moyenne",
            target=speed_target,
            details=(
                "La vitesse moyenne de l'activité "
                "n'est pas disponible."
            ),
        )

    actual_kmh = (
        float(activity.average_speed_mps)
        * 3.6
    )

    return _compare_range(
        key="average_speed",
        label="Vitesse moyenne",
        target=speed_target,
        actual=actual_kmh,
    )


def _assess_average_pace(
    session: TrainingSession,
    activity: Activity | None,
    *,
    structured_intervals: bool,
) -> NumericMetricAssessment:
    target = _find_vma_target(
        session,
    )

    pace_target = _derived_pace_target(
        target,
    )

    if pace_target is None:
        return _not_applicable(
            key="average_pace",
            label="Allure moyenne",
            details=(
                "Aucune cible d'allure structurée "
                "n'est disponible pour cette séance."
            ),
        )

    if structured_intervals:
        return _not_applicable(
            key="average_pace",
            label="Allure moyenne",
            target=pace_target,
            details=(
                "L'allure moyenne globale n'est pas "
                "utilisée pour juger une séance fractionnée."
            ),
        )

    if activity is None:
        return _insufficient(
            key="average_pace",
            label="Allure moyenne",
            target=pace_target,
            details="Aucune activité associée à la séance.",
        )

    speed_mps = activity.average_speed_mps

    if speed_mps is None or speed_mps <= 0:
        return _insufficient(
            key="average_pace",
            label="Allure moyenne",
            target=pace_target,
            details=(
                "La vitesse nécessaire au calcul "
                "de l'allure n'est pas disponible."
            ),
        )

    actual_seconds_per_km = (
        1000.0
        / float(speed_mps)
    )

    return _compare_range(
        key="average_pace",
        label="Allure moyenne",
        target=pace_target,
        actual=actual_seconds_per_km,
    )



def _moving_time_in_range(
    *,
    times,
    values,
    speeds,
    minimum: float,
    maximum: float,
):
    """Calcule l'adhérence uniquement pendant le temps actif.

    Le stream ``time`` représente le temps écoulé, pauses
    comprises. Pour une séance continue, chaque intervalle
    temporel est conservé uniquement lorsque la vitesse au
    début de l'intervalle est strictement positive.

    La timeline est ensuite compactée afin que les pauses ne
    participent ni au numérateur ni au dénominateur.
    """

    compact_times = [0.0]
    compact_values = []

    elapsed_active = 0.0

    size = min(
        len(times),
        len(values),
        len(speeds),
    )

    for index in range(size - 1):
        try:
            current_time = float(
                times[index]
            )

            next_time = float(
                times[index + 1]
            )

            value = float(
                values[index]
            )

            speed = float(
                speeds[index]
            )

        except (
            TypeError,
            ValueError,
        ):
            continue

        delta = (
            next_time
            - current_time
        )

        if (
            delta <= 0
            or delta > 10
        ):
            continue

        if speed <= 0:
            continue

        compact_values.append(
            value
        )

        elapsed_active += delta

        compact_times.append(
            elapsed_active
        )

    if not compact_values:
        return calculate_time_in_range(
            (),
            (),
            minimum=minimum,
            maximum=maximum,
        )

    # calculate_time_in_range() interprète la valeur située à
    # l'index i sur l'intervalle [time[i], time[i + 1]).
    #
    # Il faut donc N + 1 timestamps pour N intervalles actifs.
    # La dernière valeur est uniquement ajoutée pour conserver
    # un alignement compatible avec le contrat du helper.
    compact_values.append(
        compact_values[-1]
    )

    return calculate_time_in_range(
        compact_times,
        compact_values,
        minimum=minimum,
        maximum=maximum,
    )

def _assess_time_in_heart_rate_target(
    session: TrainingSession,
    activity_detail: ActivityDetail | None,
    *,
    structured_intervals: bool,
    thresholds: TargetAdherenceThresholds,
) -> NumericMetricAssessment:
    target = _find_target(
        session,
        reference="heart_rate",
    )

    if target is None:
        target = _find_target(
            session,
            reference="heart_rate_reserve",
        )

    if target is None:
        return _not_applicable(
            key="time_in_heart_rate_target",
            label="Temps dans la cible cardiaque",
            details=(
                "Aucune cible cardiaque absolue structurée "
                "n'est prescrite pour cette séance."
            ),
        )

    adherence_target = NumericTarget(
        minimum=thresholds.compliant_percent,
        maximum=100.0,
        unit="%",
    )

    if structured_intervals:
        return _not_applicable(
            key="time_in_heart_rate_target",
            label="Temps dans la cible cardiaque",
            target=adherence_target,
            details=(
                "Le temps global dans la cible cardiaque "
                "n'est pas utilisé pour juger une séance "
                "fractionnée."
            ),
        )

    if activity_detail is None:
        return _insufficient(
            key="time_in_heart_rate_target",
            label="Temps dans la cible cardiaque",
            target=adherence_target,
            details=(
                "Les streams détaillés de l'activité "
                "ne sont pas disponibles."
            ),
        )

    time_stream = activity_detail.streams.time

    heart_rate_stream = (
        activity_detail.streams.heartrate
    )

    velocity_stream = (
        activity_detail.streams.velocity_smooth
    )

    if (
        time_stream is None
        or heart_rate_stream is None
    ):
        return _insufficient(
            key="time_in_heart_rate_target",
            label="Temps dans la cible cardiaque",
            target=adherence_target,
            details=(
                "Les streams temps et fréquence cardiaque "
                "sont requis."
            ),
        )

    if velocity_stream is None:
        analysis = calculate_time_in_range(
            time_stream.data,
            heart_rate_stream.data,
            minimum=float(target["minimum"]),
            maximum=float(target["maximum"]),
        )

    else:
        analysis = _moving_time_in_range(
            times=time_stream.data,
            values=heart_rate_stream.data,
            speeds=velocity_stream.data,
            minimum=float(target["minimum"]),
            maximum=float(target["maximum"]),
        )

    return _adherence_metric(
        key="time_in_heart_rate_target",
        label="Temps dans la cible cardiaque",
        analysis=analysis,
        thresholds=thresholds,
        target_description=(
            f'{target["minimum"]:.0f}'
            f'–{target["maximum"]:.0f} '
            f'{target["unit"]}'
        ),
    )


def _assess_time_in_speed_target(
    session: TrainingSession,
    activity_detail: ActivityDetail | None,
    *,
    structured_intervals: bool,
    thresholds: TargetAdherenceThresholds,
) -> NumericMetricAssessment:
    vma_target = _find_vma_target(
        session
    )

    speed_target = _derived_speed_target(
        vma_target
    )

    if speed_target is None:
        return _not_applicable(
            key="time_in_pace_target",
            label="Temps dans la cible d'allure",
            details=(
                "Aucune cible d'allure structurée "
                "n'est disponible pour cette séance."
            ),
        )

    adherence_target = NumericTarget(
        minimum=thresholds.compliant_percent,
        maximum=100.0,
        unit="%",
    )

    if structured_intervals:
        return _not_applicable(
            key="time_in_pace_target",
            label="Temps dans la cible d'allure",
            target=adherence_target,
            details=(
                "Le temps global dans la cible d'allure "
                "n'est pas utilisé pour juger une séance "
                "fractionnée."
            ),
        )

    if activity_detail is None:
        return _insufficient(
            key="time_in_pace_target",
            label="Temps dans la cible d'allure",
            target=adherence_target,
            details=(
                "Les streams détaillés de l'activité "
                "ne sont pas disponibles."
            ),
        )

    time_stream = activity_detail.streams.time
    velocity_stream = (
        activity_detail.streams.velocity_smooth
    )

    if (
        time_stream is None
        or velocity_stream is None
    ):
        return _insufficient(
            key="time_in_pace_target",
            label="Temps dans la cible d'allure",
            target=adherence_target,
            details=(
                "Les streams temps et vitesse "
                "sont requis."
            ),
        )

    minimum_mps = (
        speed_target.minimum / 3.6
    )

    maximum_mps = (
        speed_target.maximum / 3.6
    )

    analysis = calculate_time_in_range(
        time_stream.data,
        velocity_stream.data,
        minimum=minimum_mps,
        maximum=maximum_mps,
    )

    return _adherence_metric(
        key="time_in_pace_target",
        label="Temps dans la cible d'allure",
        analysis=analysis,
        thresholds=thresholds,
        target_description=(
            f"{speed_target.minimum:.2f}"
            f"–{speed_target.maximum:.2f} km/h"
        ),
    )


def _adherence_metric(
    *,
    key: str,
    label: str,
    analysis,
    thresholds: TargetAdherenceThresholds,
    target_description: str,
) -> NumericMetricAssessment:
    target = NumericTarget(
        minimum=thresholds.compliant_percent,
        maximum=100.0,
        unit="%",
    )

    if not analysis.has_data:
        return _insufficient(
            key=key,
            label=label,
            target=target,
            details=(
                "Aucune durée de stream exploitable "
                "n'est disponible."
            ),
        )

    percent = analysis.in_range_percent

    if percent is None:
        return _insufficient(
            key=key,
            label=label,
            target=target,
            details=(
                "Aucune durée de stream exploitable "
                "n'est disponible."
            ),
        )

    if percent >= thresholds.compliant_percent:
        status = AssessmentStatus.COMPLIANT
    elif percent >= thresholds.partial_percent:
        status = AssessmentStatus.PARTIAL
    else:
        status = AssessmentStatus.NON_COMPLIANT

    delta = min(
        0.0,
        percent - thresholds.compliant_percent,
    )

    return NumericMetricAssessment(
        key=key,
        label=label,
        status=status,
        target=target,
        actual_value=round(
            percent,
            2,
        ),
        delta=round(
            delta,
            2,
        ),
        delta_percent=None,
        details=(
            f"Cible physiologique : "
            f"{target_description}. "
            f"Temps exploitable : "
            f"{analysis.valid_duration_seconds:.0f} s. "
            f"Temps dans cible : "
            f"{analysis.in_range_duration_seconds:.0f} s."
        ),
    )


def _compare_range(
    *,
    key: str,
    label: str,
    target: NumericTarget,
    actual: float,
) -> NumericMetricAssessment:
    """Compare une valeur à une plage prescrite.

    Dans la plage :
    - delta = 0 ;
    - delta_percent = 0 ;
    - COMPLIANT.

    Hors plage, l'écart est calculé par rapport à la borne
    la plus proche.
    """

    if (
        target.minimum
        <= actual
        <= target.maximum
    ):
        return NumericMetricAssessment(
            key=key,
            label=label,
            status=AssessmentStatus.COMPLIANT,
            target=target,
            actual_value=round(
                actual,
                2,
            ),
            delta=0.0,
            delta_percent=0.0,
        )

    if actual < target.minimum:
        boundary = target.minimum
    else:
        boundary = target.maximum

    delta = actual - boundary

    delta_percent = (
        delta
        / boundary
        * 100.0
    )

    if (
        abs(delta_percent)
        <= RANGE_PARTIAL_TOLERANCE_PERCENT
    ):
        status = AssessmentStatus.PARTIAL
    else:
        status = AssessmentStatus.NON_COMPLIANT

    return NumericMetricAssessment(
        key=key,
        label=label,
        status=status,
        target=target,
        actual_value=round(
            actual,
            2,
        ),
        delta=round(
            delta,
            2,
        ),
        delta_percent=round(
            delta_percent,
            2,
        ),
    )


def _find_vma_target(
    session: TrainingSession,
) -> dict[str, Any] | None:
    return _find_target(
        session,
        reference="vma_percent",
    )


def _find_target(
    session: TrainingSession,
    *,
    reference: str,
) -> dict[str, Any] | None:
    prescription = session.prescription

    if not isinstance(
        prescription,
        dict,
    ):
        return None

    intensity = prescription.get(
        "intensity"
    )

    if not isinstance(
        intensity,
        dict,
    ):
        return None

    targets = intensity.get(
        "targets"
    )

    if not isinstance(
        targets,
        list,
    ):
        return None

    for raw_target in targets:
        if not isinstance(
            raw_target,
            dict,
        ):
            continue

        if (
            raw_target.get("reference")
            != reference
        ):
            continue

        minimum = raw_target.get(
            "minimum"
        )
        maximum = raw_target.get(
            "maximum"
        )
        unit = raw_target.get(
            "unit"
        )

        if not isinstance(
            minimum,
            (int, float),
        ):
            continue

        if not isinstance(
            maximum,
            (int, float),
        ):
            continue

        if not isinstance(
            unit,
            str,
        ):
            continue

        return raw_target

    return None


def _derived_speed_target(
    target: dict[str, Any] | None,
) -> NumericTarget | None:
    if target is None:
        return None

    derived = target.get(
        "derived"
    )

    if not isinstance(
        derived,
        dict,
    ):
        return None

    speed = derived.get(
        "speed_kmh"
    )

    if not isinstance(
        speed,
        dict,
    ):
        return None

    minimum = speed.get(
        "minimum"
    )
    maximum = speed.get(
        "maximum"
    )

    if not isinstance(
        minimum,
        (int, float),
    ):
        return None

    if not isinstance(
        maximum,
        (int, float),
    ):
        return None

    return NumericTarget(
        minimum=float(minimum),
        maximum=float(maximum),
        unit="km/h",
    )


def _derived_pace_target(
    target: dict[str, Any] | None,
) -> NumericTarget | None:
    if target is None:
        return None

    derived = target.get(
        "derived"
    )

    if not isinstance(
        derived,
        dict,
    ):
        return None

    pace = derived.get(
        "pace_seconds_per_km"
    )

    if not isinstance(
        pace,
        dict,
    ):
        return None

    fastest = pace.get(
        "fastest"
    )
    slowest = pace.get(
        "slowest"
    )

    if not isinstance(
        fastest,
        (int, float),
    ):
        return None

    if not isinstance(
        slowest,
        (int, float),
    ):
        return None

    return NumericTarget(
        minimum=float(fastest),
        maximum=float(slowest),
        unit="s/km",
    )


def _has_structured_intervals(
    session: TrainingSession,
) -> bool:
    prescription = session.prescription

    if not isinstance(
        prescription,
        dict,
    ):
        return False

    structure = prescription.get(
        "work_structure"
    )

    if not isinstance(
        structure,
        dict,
    ):
        return False

    intervals = structure.get(
        "intervals"
    )

    return (
        isinstance(intervals, list)
        and len(intervals) > 0
    )


def _not_applicable(
    *,
    key: str,
    label: str,
    details: str,
    target: NumericTarget | None = None,
) -> NumericMetricAssessment:
    return NumericMetricAssessment(
        key=key,
        label=label,
        status=AssessmentStatus.NOT_APPLICABLE,
        target=target,
        details=details,
    )


def _insufficient(
    *,
    key: str,
    label: str,
    target: NumericTarget,
    details: str,
) -> NumericMetricAssessment:
    return NumericMetricAssessment(
        key=key,
        label=label,
        status=AssessmentStatus.INSUFFICIENT_DATA,
        target=target,
        details=details,
    )
