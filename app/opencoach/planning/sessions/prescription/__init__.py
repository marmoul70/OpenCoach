"""Prescription déterministe des séances OpenCoach."""

from .intervals import (
    CircuitStep,
    CircuitStepType,
    WorkCircuit,
    WorkDurationUnit,
    WorkInterval,
    WorkStructure,
    WorkStructureType,
    build_work_structure,
)
from .models import (
    IntensityRange,
    IntensityReference,
    SessionIntensityPrescription,
)
from .physiological import (
    INTENSITY_POLICIES,
    StimulusIntensityPolicy,
    build_intensity_prescription,
    validate_intensity_policy_catalog,
)


__all__ = [
    "INTENSITY_POLICIES",
    "IntensityRange",
    "IntensityReference",
    "SessionIntensityPrescription",
    "StimulusIntensityPolicy",
    "CircuitStep",
    "CircuitStepType",
    "WorkCircuit",
    "WorkDurationUnit",
    "WorkInterval",
    "WorkStructure",
    "WorkStructureType",
    "build_intensity_prescription",
    "build_work_structure",
    "validate_intensity_policy_catalog",
]
