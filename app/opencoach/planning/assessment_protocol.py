from dataclasses import dataclass
from typing import Literal

from opencoach.models import (
    PhysiologicalMetric,
)

from .assessment_need import (
    AssessmentType,
)


ProtocolIntensity = Literal[
    "submaximal",
    "maximal",
]

ProtocolEnvironment = Literal[
    "flat",
    "track",
    "hill",
    "laboratory",
    "any",
]


@dataclass(frozen=True)
class AssessmentProtocol:
    """Protocole permettant de calibrer une ou plusieurs métriques."""

    protocol_id: str
    name: str

    assessment_types: tuple[
        AssessmentType,
        ...
    ]

    metrics: tuple[
        PhysiologicalMetric,
        ...
    ]

    intensity: ProtocolIntensity
    environment: ProtocolEnvironment

    estimated_duration_minutes: int

    requires_precise_distance: bool
    requires_external_equipment: bool

    description: str


ASSESSMENT_PROTOCOLS: tuple[
    AssessmentProtocol,
    ...
] = (
    AssessmentProtocol(
        protocol_id="vameval",
        name="VAMEVAL",
        assessment_types=(
            "vma_calibration",
            "max_heart_rate_calibration",
        ),
        metrics=(
            "vma",
            "max_heart_rate",
        ),
        intensity="maximal",
        environment="track",
        estimated_duration_minutes=45,
        requires_precise_distance=True,
        requires_external_equipment=False,
        description=(
            "Test progressif sur piste permettant d'estimer la VMA "
            "et pouvant fournir une observation de FC maximale."
        ),
    ),
    AssessmentProtocol(
        protocol_id="half_cooper",
        name="Demi-Cooper",
        assessment_types=(
            "vma_calibration",
            "max_heart_rate_calibration",
        ),
        metrics=(
            "vma",
            "max_heart_rate",
        ),
        intensity="maximal",
        environment="flat",
        estimated_duration_minutes=40,
        requires_precise_distance=True,
        requires_external_equipment=False,
        description=(
            "Effort maximal de six minutes sur terrain plat et mesuré."
        ),
    ),
    AssessmentProtocol(
        protocol_id="twenty_minute_threshold",
        name="Test seuil 20 minutes",
        assessment_types=(
            "threshold_calibration",
        ),
        metrics=(
            "threshold_heart_rate_2",
        ),
        intensity="maximal",
        environment="flat",
        estimated_duration_minutes=50,
        requires_precise_distance=False,
        requires_external_equipment=False,
        description=(
            "Effort soutenu permettant d'obtenir une estimation terrain "
            "du seuil supérieur."
        ),
    ),
    AssessmentProtocol(
        protocol_id="laboratory_threshold",
        name="Test de seuil en laboratoire",
        assessment_types=(
            "threshold_calibration",
            "max_heart_rate_calibration",
        ),
        metrics=(
            "threshold_heart_rate_1",
            "threshold_heart_rate_2",
            "max_heart_rate",
        ),
        intensity="maximal",
        environment="laboratory",
        estimated_duration_minutes=60,
        requires_precise_distance=False,
        requires_external_equipment=True,
        description=(
            "Évaluation encadrée permettant une mesure précise "
            "des seuils physiologiques."
        ),
    ),
)


def get_assessment_protocols(
    assessment_type: AssessmentType,
) -> tuple[AssessmentProtocol, ...]:
    """Retourne les protocoles capables de répondre à un besoin."""

    return tuple(
        protocol
        for protocol in ASSESSMENT_PROTOCOLS
        if assessment_type
        in protocol.assessment_types
    )


def get_assessment_protocol(
    protocol_id: str,
) -> AssessmentProtocol | None:
    """Retourne un protocole par identifiant."""

    normalized = (
        protocol_id.strip().lower()
    )

    return next(
        (
            protocol
            for protocol in ASSESSMENT_PROTOCOLS
            if protocol.protocol_id
            == normalized
        ),
        None,
    )
