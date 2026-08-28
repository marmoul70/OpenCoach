"""Évaluation déterministe de la structure d'un fractionné."""

from __future__ import annotations

from math import sqrt

from opencoach.models import (
    ActivityDetail,
    TrainingSession,
)

from .interval_detection import (
    ObservedRepetition,
    detect_repetitions,
)
from .interval_prescription import (
    IntervalSetPrescription,
    parse_structured_session_prescription,
)
from .metric import (
    NumericMetricAssessment,
    NumericTarget,
)
from .models import (
    SessionExecutionStructureAssessment,
)
from .status import AssessmentStatus
from .thresholds import (
    DEFAULT_STRUCTURE_THRESHOLDS,
    StructureAssessmentThresholds,
)


def assess_session_structure(
    session: TrainingSession,
    activity_detail: ActivityDetail | None,
    *,
    thresholds: StructureAssessmentThresholds = (
        DEFAULT_STRUCTURE_THRESHOLDS
    ),
) -> SessionExecutionStructureAssessment:
    """Évalue la structure réellement exécutée."""

    prescription = (
        parse_structured_session_prescription(
            session
        )
    )

    if prescription is None:
        return _not_applicable_structure()

    if len(prescription.interval_sets) != 1:
        return _unsupported_multi_set_structure()

    interval_set = prescription.interval_sets[0]

    if activity_detail is None:
        return _missing_detail_structure(
            interval_set
        )

    detection = detect_repetitions(
        activity_detail,
        interval_set,
    )

    repetitions = detection.repetitions

    return SessionExecutionStructureAssessment(
        repetition_count=_assess_repetition_count(
            expected=interval_set.repetitions,
            actual=len(repetitions),
            thresholds=thresholds,
        ),
        work_duration=_assess_work_duration(
            interval_set,
            repetitions,
            thresholds=thresholds,
        ),
        work_distance=_assess_work_distance(
            interval_set,
            repetitions,
            thresholds=thresholds,
        ),
        recovery_duration=_assess_recovery_duration(
            interval_set,
            repetitions,
            thresholds=thresholds,
        ),
        repetition_regularity=_assess_regularity(
            repetitions,
            thresholds=thresholds,
        ),
        repetition_degradation=_assess_degradation(
            repetitions,
            thresholds=thresholds,
        ),
    )


def _assess_repetition_count(
    *,
    expected: int,
    actual: int,
    thresholds: StructureAssessmentThresholds,
) -> NumericMetricAssessment:
    completion = (
        actual
        / expected
        * 100.0
    )

    if actual == expected:
        status = AssessmentStatus.COMPLIANT
    elif (
        completion
        >= thresholds.repetition_partial_percent
    ):
        status = AssessmentStatus.PARTIAL
    else:
        status = AssessmentStatus.NON_COMPLIANT

    return NumericMetricAssessment(
        key="repetition_count",
        label="Nombre de répétitions",
        status=status,
        target=NumericTarget.exact(
            float(expected),
            "rep",
        ),
        actual_value=float(actual),
        delta=float(
            actual - expected
        ),
        delta_percent=round(
            completion - 100.0,
            2,
        ),
    )


def _assess_work_distance(
    prescription: IntervalSetPrescription,
    repetitions: tuple[
        ObservedRepetition,
        ...,
    ],
    *,
    thresholds: StructureAssessmentThresholds,
) -> NumericMetricAssessment:
    expected = prescription.work_distance_m

    if expected is None:
        return _not_applicable_metric(
            key="work_distance",
            label="Distance des répétitions",
            details=(
                "La séance n'est pas prescrite "
                "par distance."
            ),
        )

    distances = [
        repetition.distance_m
        for repetition in repetitions
        if repetition.distance_m is not None
    ]

    if not distances:
        return _insufficient_metric(
            key="work_distance",
            label="Distance des répétitions",
            target=NumericTarget.exact(
                expected,
                "m",
            ),
            details=(
                "Aucune distance de répétition "
                "n'a été détectée."
            ),
        )

    actual = (
        sum(distances)
        / len(distances)
    )

    return _compare_exact(
        key="work_distance",
        label="Distance moyenne des répétitions",
        expected=expected,
        actual=actual,
        unit="m",
        compliant_percent=(
            thresholds.work_distance_compliant_percent
        ),
        partial_percent=(
            thresholds.work_distance_partial_percent
        ),
    )


def _assess_work_duration(
    prescription: IntervalSetPrescription,
    repetitions: tuple[
        ObservedRepetition,
        ...,
    ],
    *,
    thresholds: StructureAssessmentThresholds,
) -> NumericMetricAssessment:
    if not repetitions:
        return _insufficient_metric(
            key="work_duration",
            label="Durée des répétitions",
            target=_duration_target(
                prescription
            ),
            details=(
                "Aucune répétition détectée."
            ),
        )

    durations = [
        repetition.duration_seconds
        for repetition in repetitions
    ]

    actual = (
        sum(durations)
        / len(durations)
    )

    target = prescription.repetition_target

    if (
        target is not None
        and target.target_duration_min_seconds
        is not None
        and target.target_duration_max_seconds
        is not None
    ):
        return _compare_range(
            key="work_duration",
            label="Chrono moyen des répétitions",
            minimum=(
                target.target_duration_min_seconds
            ),
            maximum=(
                target.target_duration_max_seconds
            ),
            actual=actual,
            unit="s",
            partial_percent=(
                thresholds.work_duration_partial_percent
            ),
        )

    if prescription.work_duration_seconds is not None:
        return _compare_exact(
            key="work_duration",
            label="Durée moyenne des répétitions",
            expected=(
                prescription.work_duration_seconds
            ),
            actual=actual,
            unit="s",
            compliant_percent=(
                thresholds.work_duration_partial_percent
                / 2.0
            ),
            partial_percent=(
                thresholds.work_duration_partial_percent
            ),
        )

    return _not_applicable_metric(
        key="work_duration",
        label="Durée des répétitions",
        details=(
            "Aucune cible de durée n'est disponible."
        ),
    )


def _assess_recovery_duration(
    prescription: IntervalSetPrescription,
    repetitions: tuple[
        ObservedRepetition,
        ...,
    ],
    *,
    thresholds: StructureAssessmentThresholds,
) -> NumericMetricAssessment:
    expected = (
        prescription.recovery_duration_seconds
    )

    if expected is None:
        return _not_applicable_metric(
            key="recovery_duration",
            label="Durée de récupération",
            details=(
                "Aucune récupération structurée "
                "n'est prescrite."
            ),
        )

    if len(repetitions) < 2:
        return _insufficient_metric(
            key="recovery_duration",
            label="Durée de récupération",
            target=NumericTarget.exact(
                expected,
                "s",
            ),
            details=(
                "Au moins deux répétitions sont "
                "nécessaires pour mesurer la récupération."
            ),
        )

    recoveries = []

    for current, following in zip(
        repetitions,
        repetitions[1:],
        strict=False,
    ):
        recovery = (
            following.start_time_seconds
            - current.end_time_seconds
        )

        if recovery >= 0:
            recoveries.append(
                float(recovery)
            )

    if not recoveries:
        return _insufficient_metric(
            key="recovery_duration",
            label="Durée de récupération",
            target=NumericTarget.exact(
                expected,
                "s",
            ),
            details=(
                "Les temps de récupération "
                "ne sont pas exploitables."
            ),
        )

    actual = (
        sum(recoveries)
        / len(recoveries)
    )

    return _compare_exact(
        key="recovery_duration",
        label="Récupération moyenne",
        expected=expected,
        actual=actual,
        unit="s",
        compliant_percent=(
            thresholds.recovery_compliant_percent
        ),
        partial_percent=(
            thresholds.recovery_partial_percent
        ),
    )


def _assess_regularity(
    repetitions: tuple[
        ObservedRepetition,
        ...,
    ],
    *,
    thresholds: StructureAssessmentThresholds,
) -> NumericMetricAssessment:
    if len(repetitions) < 2:
        return _insufficient_metric(
            key="repetition_regularity",
            label="Régularité des répétitions",
            target=NumericTarget(
                minimum=0.0,
                maximum=(
                    thresholds.regularity_compliant_percent
                ),
                unit="%",
            ),
            details=(
                "Au moins deux répétitions sont "
                "nécessaires pour mesurer la régularité."
            ),
        )

    durations = [
        repetition.duration_seconds
        for repetition in repetitions
    ]

    mean = (
        sum(durations)
        / len(durations)
    )

    if mean <= 0:
        return _insufficient_metric(
            key="repetition_regularity",
            label="Régularité des répétitions",
            target=NumericTarget(
                minimum=0.0,
                maximum=(
                    thresholds.regularity_compliant_percent
                ),
                unit="%",
            ),
            details="Durées non exploitables.",
        )

    variance = (
        sum(
            (duration - mean) ** 2
            for duration in durations
        )
        / len(durations)
    )

    cv = (
        sqrt(variance)
        / mean
        * 100.0
    )

    if (
        cv
        <= thresholds.regularity_compliant_percent
    ):
        status = AssessmentStatus.COMPLIANT
    elif (
        cv
        <= thresholds.regularity_partial_percent
    ):
        status = AssessmentStatus.PARTIAL
    else:
        status = AssessmentStatus.NON_COMPLIANT

    return NumericMetricAssessment(
        key="repetition_regularity",
        label="Régularité des répétitions",
        status=status,
        target=NumericTarget(
            minimum=0.0,
            maximum=(
                thresholds.regularity_compliant_percent
            ),
            unit="%",
        ),
        actual_value=round(
            cv,
            2,
        ),
        delta=round(
            max(
                0.0,
                cv
                - thresholds.regularity_compliant_percent,
            ),
            2,
        ),
        details=(
            "Coefficient de variation "
            "des chronos de répétition."
        ),
    )


def _assess_degradation(
    repetitions: tuple[
        ObservedRepetition,
        ...,
    ],
    *,
    thresholds: StructureAssessmentThresholds,
) -> NumericMetricAssessment:
    if len(repetitions) < 4:
        return _insufficient_metric(
            key="repetition_degradation",
            label="Dégradation des répétitions",
            target=NumericTarget(
                minimum=0.0,
                maximum=(
                    thresholds.degradation_compliant_percent
                ),
                unit="%",
            ),
            details=(
                "Au moins quatre répétitions sont "
                "nécessaires pour mesurer la dégradation."
            ),
        )

    midpoint = (
        len(repetitions)
        // 2
    )

    first = repetitions[:midpoint]
    second = repetitions[-midpoint:]

    first_mean = (
        sum(
            repetition.duration_seconds
            for repetition in first
        )
        / len(first)
    )

    second_mean = (
        sum(
            repetition.duration_seconds
            for repetition in second
        )
        / len(second)
    )

    if first_mean <= 0:
        return _insufficient_metric(
            key="repetition_degradation",
            label="Dégradation des répétitions",
            target=NumericTarget(
                minimum=0.0,
                maximum=(
                    thresholds.degradation_compliant_percent
                ),
                unit="%",
            ),
            details="Chronos non exploitables.",
        )

    raw_degradation = (
        (second_mean - first_mean)
        / first_mean
        * 100.0
    )

    degradation = max(
        0.0,
        raw_degradation,
    )

    if (
        degradation
        <= thresholds.degradation_compliant_percent
    ):
        status = AssessmentStatus.COMPLIANT
    elif (
        degradation
        <= thresholds.degradation_partial_percent
    ):
        status = AssessmentStatus.PARTIAL
    else:
        status = AssessmentStatus.NON_COMPLIANT

    return NumericMetricAssessment(
        key="repetition_degradation",
        label="Dégradation des répétitions",
        status=status,
        target=NumericTarget(
            minimum=0.0,
            maximum=(
                thresholds.degradation_compliant_percent
            ),
            unit="%",
        ),
        actual_value=round(
            degradation,
            2,
        ),
        delta=round(
            max(
                0.0,
                degradation
                - thresholds.degradation_compliant_percent,
            ),
            2,
        ),
        details=(
            "Écart moyen de chrono entre "
            "la première et la seconde moitié."
        ),
    )


def _compare_exact(
    *,
    key: str,
    label: str,
    expected: float,
    actual: float,
    unit: str,
    compliant_percent: float,
    partial_percent: float,
) -> NumericMetricAssessment:
    delta = (
        actual - expected
    )

    delta_percent = (
        delta
        / expected
        * 100.0
    )

    absolute = abs(
        delta_percent
    )

    if absolute <= compliant_percent:
        status = AssessmentStatus.COMPLIANT
    elif absolute <= partial_percent:
        status = AssessmentStatus.PARTIAL
    else:
        status = AssessmentStatus.NON_COMPLIANT

    return NumericMetricAssessment(
        key=key,
        label=label,
        status=status,
        target=NumericTarget.exact(
            expected,
            unit,
        ),
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


def _compare_range(
    *,
    key: str,
    label: str,
    minimum: float,
    maximum: float,
    actual: float,
    unit: str,
    partial_percent: float,
) -> NumericMetricAssessment:
    target = NumericTarget(
        minimum=minimum,
        maximum=maximum,
        unit=unit,
    )

    if minimum <= actual <= maximum:
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

    boundary = (
        minimum
        if actual < minimum
        else maximum
    )

    delta = (
        actual - boundary
    )

    delta_percent = (
        delta
        / boundary
        * 100.0
    )

    status = (
        AssessmentStatus.PARTIAL
        if abs(delta_percent)
        <= partial_percent
        else AssessmentStatus.NON_COMPLIANT
    )

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


def _duration_target(
    prescription: IntervalSetPrescription,
) -> NumericTarget | None:
    target = prescription.repetition_target

    if (
        target is not None
        and target.target_duration_min_seconds
        is not None
        and target.target_duration_max_seconds
        is not None
    ):
        return NumericTarget(
            minimum=(
                target.target_duration_min_seconds
            ),
            maximum=(
                target.target_duration_max_seconds
            ),
            unit="s",
        )

    if prescription.work_duration_seconds is not None:
        return NumericTarget.exact(
            prescription.work_duration_seconds,
            "s",
        )

    return None


def _not_applicable_structure(
) -> SessionExecutionStructureAssessment:
    metric = lambda key, label: _not_applicable_metric(
        key=key,
        label=label,
        details=(
            "Cette séance ne contient pas "
            "de structure fractionnée."
        ),
    )

    return SessionExecutionStructureAssessment(
        repetition_count=metric(
            "repetition_count",
            "Nombre de répétitions",
        ),
        work_duration=metric(
            "work_duration",
            "Durée des répétitions",
        ),
        work_distance=metric(
            "work_distance",
            "Distance des répétitions",
        ),
        recovery_duration=metric(
            "recovery_duration",
            "Durée de récupération",
        ),
        repetition_regularity=metric(
            "repetition_regularity",
            "Régularité des répétitions",
        ),
        repetition_degradation=metric(
            "repetition_degradation",
            "Dégradation des répétitions",
        ),
    )


def _missing_detail_structure(
    prescription: IntervalSetPrescription,
) -> SessionExecutionStructureAssessment:
    expected = NumericTarget.exact(
        float(prescription.repetitions),
        "rep",
    )

    return SessionExecutionStructureAssessment(
        repetition_count=_insufficient_metric(
            key="repetition_count",
            label="Nombre de répétitions",
            target=expected,
            details=(
                "Les détails de l'activité "
                "ne sont pas disponibles."
            ),
        ),
        work_duration=_insufficient_metric(
            key="work_duration",
            label="Durée des répétitions",
            target=_duration_target(
                prescription
            ),
            details=(
                "Les détails de l'activité "
                "ne sont pas disponibles."
            ),
        ),
        work_distance=_insufficient_metric(
            key="work_distance",
            label="Distance des répétitions",
            target=(
                NumericTarget.exact(
                    prescription.work_distance_m,
                    "m",
                )
                if prescription.work_distance_m
                is not None
                else None
            ),
            details=(
                "Les détails de l'activité "
                "ne sont pas disponibles."
            ),
        ),
        recovery_duration=_insufficient_metric(
            key="recovery_duration",
            label="Durée de récupération",
            target=(
                NumericTarget.exact(
                    prescription.recovery_duration_seconds,
                    "s",
                )
                if prescription.recovery_duration_seconds
                is not None
                else None
            ),
            details=(
                "Les détails de l'activité "
                "ne sont pas disponibles."
            ),
        ),
        repetition_regularity=_insufficient_metric(
            key="repetition_regularity",
            label="Régularité des répétitions",
            target=None,
            details=(
                "Les détails de l'activité "
                "ne sont pas disponibles."
            ),
        ),
        repetition_degradation=_insufficient_metric(
            key="repetition_degradation",
            label="Dégradation des répétitions",
            target=None,
            details=(
                "Les détails de l'activité "
                "ne sont pas disponibles."
            ),
        ),
    )


def _unsupported_multi_set_structure(
) -> SessionExecutionStructureAssessment:
    def metric(
        key: str,
        label: str,
    ) -> NumericMetricAssessment:
        return _insufficient_metric(
            key=key,
            label=label,
            target=None,
            details=(
                "L'analyse de plusieurs groupes "
                "d'intervalles distincts n'est pas "
                "encore supportée."
            ),
        )

    return SessionExecutionStructureAssessment(
        repetition_count=metric(
            "repetition_count",
            "Nombre de répétitions",
        ),
        work_duration=metric(
            "work_duration",
            "Durée des répétitions",
        ),
        work_distance=metric(
            "work_distance",
            "Distance des répétitions",
        ),
        recovery_duration=metric(
            "recovery_duration",
            "Durée de récupération",
        ),
        repetition_regularity=metric(
            "repetition_regularity",
            "Régularité des répétitions",
        ),
        repetition_degradation=metric(
            "repetition_degradation",
            "Dégradation des répétitions",
        ),
    )


def _not_applicable_metric(
    *,
    key: str,
    label: str,
    details: str,
) -> NumericMetricAssessment:
    return NumericMetricAssessment(
        key=key,
        label=label,
        status=AssessmentStatus.NOT_APPLICABLE,
        details=details,
    )


def _insufficient_metric(
    *,
    key: str,
    label: str,
    target: NumericTarget | None,
    details: str,
) -> NumericMetricAssessment:
    return NumericMetricAssessment(
        key=key,
        label=label,
        status=AssessmentStatus.INSUFFICIENT_DATA,
        target=target,
        details=details,
    )
