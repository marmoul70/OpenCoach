"""Prescription structurée des séances fractionnées."""

from __future__ import annotations

from dataclasses import dataclass

from opencoach.models import TrainingSession


@dataclass(frozen=True, slots=True)
class RepetitionTarget:
    """Cible physiologique et mécanique d'une répétition."""

    distance_m: float | None = None

    target_duration_min_seconds: float | None = None
    target_duration_max_seconds: float | None = None

    vma_kmh: float | None = None
    vma_percent_min: float | None = None
    vma_percent_max: float | None = None

    def __post_init__(self) -> None:
        if (
            self.distance_m is not None
            and self.distance_m <= 0
        ):
            raise ValueError(
                "La distance cible d'une répétition "
                "doit être positive."
            )

        if (
            self.target_duration_min_seconds is not None
            and self.target_duration_min_seconds <= 0
        ):
            raise ValueError(
                "La durée minimale cible "
                "doit être positive."
            )

        if (
            self.target_duration_max_seconds is not None
            and self.target_duration_max_seconds <= 0
        ):
            raise ValueError(
                "La durée maximale cible "
                "doit être positive."
            )

        if (
            self.target_duration_min_seconds is not None
            and self.target_duration_max_seconds is not None
            and self.target_duration_max_seconds
            < self.target_duration_min_seconds
        ):
            raise ValueError(
                "La durée maximale cible ne peut pas "
                "être inférieure à la durée minimale."
            )


@dataclass(frozen=True, slots=True)
class IntervalSetPrescription:
    """Un groupe de répétitions prescrit."""

    repetitions: int

    work_distance_m: float | None = None
    work_duration_seconds: float | None = None

    recovery_duration_seconds: float | None = None

    repetition_target: RepetitionTarget | None = None

    def __post_init__(self) -> None:
        if self.repetitions <= 0:
            raise ValueError(
                "Le nombre de répétitions "
                "doit être positif."
            )

        if (
            self.work_distance_m is None
            and self.work_duration_seconds is None
        ):
            raise ValueError(
                "Une répétition doit être prescrite "
                "par distance ou par durée."
            )

        if (
            self.work_distance_m is not None
            and self.work_distance_m <= 0
        ):
            raise ValueError(
                "La distance de travail "
                "doit être positive."
            )

        if (
            self.work_duration_seconds is not None
            and self.work_duration_seconds <= 0
        ):
            raise ValueError(
                "La durée de travail "
                "doit être positive."
            )

        if (
            self.recovery_duration_seconds is not None
            and self.recovery_duration_seconds < 0
        ):
            raise ValueError(
                "La récupération ne peut pas être négative."
            )


@dataclass(frozen=True, slots=True)
class StructuredSessionPrescription:
    """Structure déterministe d'une séance fractionnée."""

    structure_type: str
    stimulus: str | None

    interval_sets: tuple[
        IntervalSetPrescription,
        ...,
    ]

    def __post_init__(self) -> None:
        if not self.structure_type.strip():
            raise ValueError(
                "Le type de structure "
                "ne peut pas être vide."
            )

        if not self.interval_sets:
            raise ValueError(
                "Une séance structurée doit contenir "
                "au moins un groupe d'intervalles."
            )

    @property
    def total_repetitions(self) -> int:
        """Nombre total de répétitions prescrites."""

        return sum(
            interval_set.repetitions
            for interval_set in self.interval_sets
        )


def parse_structured_session_prescription(
    session: TrainingSession,
) -> StructuredSessionPrescription | None:
    """Extrait la prescription fractionnée structurée.

    Aucun texte libre n'est interprété. Seuls les champs
    structurés de ``TrainingSession.prescription`` sont lus.
    """

    prescription = session.prescription

    if not isinstance(
        prescription,
        dict,
    ):
        return None

    work_structure = prescription.get(
        "work_structure"
    )

    if not isinstance(
        work_structure,
        dict,
    ):
        return None

    raw_intervals = work_structure.get(
        "intervals"
    )

    if not isinstance(
        raw_intervals,
        list,
    ) or not raw_intervals:
        return None

    structure_type = work_structure.get(
        "type"
    )

    if not isinstance(
        structure_type,
        str,
    ) or not structure_type.strip():
        raise ValueError(
            "work_structure.type est obligatoire "
            "pour une séance structurée."
        )

    stimulus = work_structure.get(
        "stimulus"
    )

    if stimulus is not None:
        if not isinstance(
            stimulus,
            str,
        ):
            raise ValueError(
                "work_structure.stimulus invalide."
            )

        stimulus = (
            stimulus.strip()
            or None
        )

    interval_sets = tuple(
        _parse_interval_set(
            raw_interval
        )
        for raw_interval in raw_intervals
    )

    return StructuredSessionPrescription(
        structure_type=structure_type.strip(),
        stimulus=stimulus,
        interval_sets=interval_sets,
    )


def _parse_interval_set(
    raw: object,
) -> IntervalSetPrescription:
    if not isinstance(
        raw,
        dict,
    ):
        raise ValueError(
            "Une entrée work_structure.intervals "
            "doit être un objet."
        )

    repetitions = _required_positive_int(
        raw,
        "repetitions",
    )

    work_distance_m = _optional_positive_number(
        raw.get(
            "work_distance_meters"
        ),
        field="work_distance_meters",
    )

    work_duration_seconds = _duration_to_seconds(
        raw.get("work_duration"),
        raw.get("work_unit"),
        field="work_duration",
    )

    recovery_duration_seconds = (
        _duration_to_seconds(
            raw.get("recovery_duration"),
            raw.get("recovery_unit"),
            field="recovery_duration",
            allow_zero=True,
        )
    )

    repetition_target = _parse_repetition_target(
        raw.get(
            "repetition_target"
        )
    )

    return IntervalSetPrescription(
        repetitions=repetitions,
        work_distance_m=work_distance_m,
        work_duration_seconds=(
            work_duration_seconds
        ),
        recovery_duration_seconds=(
            recovery_duration_seconds
        ),
        repetition_target=repetition_target,
    )


def _parse_repetition_target(
    raw: object,
) -> RepetitionTarget | None:
    if raw is None:
        return None

    if not isinstance(
        raw,
        dict,
    ):
        raise ValueError(
            "repetition_target doit être un objet."
        )

    distance_m = _optional_positive_number(
        raw.get(
            "distance_meters"
        ),
        field="distance_meters",
    )

    fast_seconds = _optional_positive_number(
        raw.get(
            "fast_seconds"
        ),
        field="fast_seconds",
    )

    slow_seconds = _optional_positive_number(
        raw.get(
            "slow_seconds"
        ),
        field="slow_seconds",
    )

    vma_kmh = _optional_positive_number(
        raw.get(
            "vma_kmh"
        ),
        field="vma_kmh",
    )

    vma_percent_min = _optional_positive_number(
        raw.get(
            "vma_percent_min"
        ),
        field="vma_percent_min",
    )

    vma_percent_max = _optional_positive_number(
        raw.get(
            "vma_percent_max"
        ),
        field="vma_percent_max",
    )

    return RepetitionTarget(
        distance_m=distance_m,
        target_duration_min_seconds=(
            fast_seconds
        ),
        target_duration_max_seconds=(
            slow_seconds
        ),
        vma_kmh=vma_kmh,
        vma_percent_min=vma_percent_min,
        vma_percent_max=vma_percent_max,
    )


def _duration_to_seconds(
    value: object,
    unit: object,
    *,
    field: str,
    allow_zero: bool = False,
) -> float | None:
    if value is None:
        return None

    if (
        not isinstance(
            value,
            (int, float),
        )
        or isinstance(value, bool)
    ):
        raise ValueError(
            f"{field} doit être numérique."
        )

    numeric_value = float(value)

    if allow_zero:
        if numeric_value < 0:
            raise ValueError(
                f"{field} ne peut pas être négatif."
            )
    elif numeric_value <= 0:
        raise ValueError(
            f"{field} doit être positif."
        )

    if not isinstance(
        unit,
        str,
    ):
        raise ValueError(
            f"L'unité de {field} est obligatoire."
        )

    normalized_unit = unit.strip().casefold()

    factors = {
        "second": 1.0,
        "seconds": 1.0,
        "seconde": 1.0,
        "secondes": 1.0,
        "s": 1.0,
        "minute": 60.0,
        "minutes": 60.0,
        "min": 60.0,
    }

    factor = factors.get(
        normalized_unit
    )

    if factor is None:
        raise ValueError(
            f"Unité de durée non supportée : {unit!r}."
        )

    return (
        numeric_value
        * factor
    )


def _required_positive_int(
    data: dict,
    field: str,
) -> int:
    value = data.get(
        field
    )

    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or value <= 0
    ):
        raise ValueError(
            f"{field} doit être un entier positif."
        )

    return value


def _optional_positive_number(
    value: object,
    *,
    field: str,
) -> float | None:
    if value is None:
        return None

    if (
        not isinstance(
            value,
            (int, float),
        )
        or isinstance(value, bool)
    ):
        raise ValueError(
            f"{field} doit être numérique."
        )

    result = float(
        value
    )

    if result <= 0:
        raise ValueError(
            f"{field} doit être positif."
        )

    return result
