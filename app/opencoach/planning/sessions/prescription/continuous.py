"""Construction des prescriptions continues adaptées."""

from __future__ import annotations

from opencoach.planning.physiology.snapshot import (
    PhysiologicalCalibrationSnapshot,
)
from opencoach.planning.sessions.prescription.models import (
    IntensityRange,
    SessionIntensityPrescription,
)
from opencoach.planning.sessions.prescription.physiological import (
    build_intensity_prescription,
)
from opencoach.planning.stimulus.training import (
    TrainingStimulus,
)


_CONTINUOUS_DESCRIPTIONS = {
    TrainingStimulus.RECOVERY: (
        "Séance continue de récupération."
    ),
    TrainingStimulus.AEROBIC_EASY: (
        "Endurance facile continue."
    ),
    TrainingStimulus.AEROBIC_ENDURANCE: (
        "Endurance aérobie continue."
    ),
    TrainingStimulus.LONG_ENDURANCE: (
        "Endurance longue continue."
    ),
}


def build_continuous_session_prescription(
    *,
    stimulus: TrainingStimulus,
    duration_minutes: int,
    physiology: PhysiologicalCalibrationSnapshot | None,
) -> dict:
    """Construit une prescription v1 cohérente pour un effort continu."""

    if duration_minutes <= 0:
        raise ValueError(
            "La durée d'une séance continue doit être positive."
        )

    if stimulus not in _CONTINUOUS_DESCRIPTIONS:
        raise ValueError(
            "Le stimulus demandé n'est pas supporté "
            "par le constructeur de séance continue : "
            f"{stimulus.value!r}."
        )

    intensity = build_intensity_prescription(
        stimulus=stimulus,
        physiology=physiology,
    )

    description = (
        _CONTINUOUS_DESCRIPTIONS[
            stimulus
        ]
    )

    return {
        "version": 1,
        "blocks": [],
        "work_structure": {
            "type": "continuous",
            "stimulus": stimulus.value,
            "available_minutes": duration_minutes,
            "continuous_minutes": duration_minutes,
            "description": description,
            "circuit": None,
            "intervals": [],
        },
        "intensity": (
            _serialize_intensity(
                intensity
            )
        ),
    }


def _serialize_intensity(
    prescription: SessionIntensityPrescription,
) -> dict:
    return {
        "targets": [
            _serialize_target(
                target
            )
            for target
            in prescription.targets
        ],
        "guidance": list(
            prescription.guidance
        ),
    }


def _serialize_target(
    target: IntensityRange,
) -> dict:
    result = {
        "reference": (
            target.reference.value
        ),
        "minimum": target.minimum,
        "maximum": target.maximum,
        "unit": target.unit,
        "label": target.label,
    }

    if (
        target.speed_min_kmh is not None
        and target.speed_max_kmh is not None
    ):
        result["derived"] = {
            "speed_kmh": {
                "minimum": (
                    target.speed_min_kmh
                ),
                "maximum": (
                    target.speed_max_kmh
                ),
            },
        }

    if (
        target.pace_fastest_seconds_per_km
        is not None
        and target.pace_slowest_seconds_per_km
        is not None
    ):
        derived = result.setdefault(
            "derived",
            {},
        )

        derived[
            "pace_seconds_per_km"
        ] = {
            "fastest": (
                target
                .pace_fastest_seconds_per_km
            ),
            "slowest": (
                target
                .pace_slowest_seconds_per_km
            ),
        }

    return result
