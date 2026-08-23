from typing import Any


def build_season_strategy_proposal_schema(
) -> dict[str, Any]:
    """Retourne le JSON Schema imposé au moteur de stratégie."""

    stimulus_types = [
        "aerobic_endurance",
        "long_endurance",
        "threshold",
        "vo2max",
        "race_specific",
        "hill_strength",
        "downhill_skill",
        "strength",
        "recovery",
        "physiological_assessment",
    ]

    phase_types = [
        "foundation",
        "base",
        "build",
        "specific",
        "taper",
        "recovery",
        "race",
    ]

    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "summary",
            "facts_used",
            "assumptions",
            "decisions",
            "uncertainties",
            "phases",
            "weeks",
            "revision_changes",
        ],
        "properties": {
            "summary": {
                "type": "string",
                "minLength": 1,
            },
            "facts_used": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "source_path",
                        "purpose",
                    ],
                    "properties": {
                        "source_path": {
                            "type": "string",
                            "minLength": 1,
                        },
                        "purpose": {
                            "type": "string",
                            "minLength": 1,
                        },
                    },
                },
            },
            "assumptions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "assumption_id",
                        "description",
                        "impact",
                        "affected_area",
                    ],
                    "properties": {
                        "assumption_id": {
                            "type": "string",
                            "minLength": 1,
                        },
                        "description": {
                            "type": "string",
                            "minLength": 1,
                        },
                        "impact": {
                            "type": "string",
                            "enum": [
                                "low",
                                "medium",
                                "high",
                            ],
                        },
                        "affected_area": {
                            "type": "string",
                            "minLength": 1,
                        },
                    },
                },
            },
            "decisions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "decision_type",
                        "description",
                        "rationale",
                        "based_on_facts",
                        "based_on_assumptions",
                    ],
                    "properties": {
                        "decision_type": {
                            "type": "string",
                            "enum": [
                                "phase_structure",
                                "load_progression",
                                "recovery_strategy",
                                "specificity_progression",
                                "taper_strategy",
                                "race_integration",
                                "assessment_strategy",
                                "other",
                            ],
                        },
                        "description": {
                            "type": "string",
                            "minLength": 1,
                        },
                        "rationale": {
                            "type": "string",
                            "minLength": 1,
                        },
                        "based_on_facts": {
                            "type": "array",
                            "items": {
                                "type": "string",
                            },
                        },
                        "based_on_assumptions": {
                            "type": "array",
                            "items": {
                                "type": "string",
                            },
                        },
                    },
                },
            },
            "uncertainties": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "level",
                        "description",
                        "affected_area",
                        "resolution_hint",
                    ],
                    "properties": {
                        "level": {
                            "type": "string",
                            "enum": [
                                "low",
                                "medium",
                                "high",
                            ],
                        },
                        "description": {
                            "type": "string",
                            "minLength": 1,
                        },
                        "affected_area": {
                            "type": "string",
                            "minLength": 1,
                        },
                        "resolution_hint": {
                            "type": [
                                "string",
                                "null",
                            ],
                        },
                    },
                },
            },
            "phases": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "phase_type",
                        "start_date",
                        "end_date",
                        "objective",
                        "primary_stimuli",
                    ],
                    "properties": {
                        "phase_type": {
                            "type": "string",
                            "enum": phase_types,
                        },
                        "start_date": {
                            "type": "string",
                            "format": "date",
                        },
                        "end_date": {
                            "type": "string",
                            "format": "date",
                        },
                        "objective": {
                            "type": "string",
                            "minLength": 1,
                        },
                        "primary_stimuli": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": stimulus_types,
                            },
                        },
                    },
                },
            },
            "weeks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "week_number",
                        "start_date",
                        "end_date",
                        "phase",
                        "target_load",
                        "load_min",
                        "load_max",
                        "target_duration_minutes",
                        "target_distance_km",
                        "target_elevation_gain_m",
                        "primary_stimuli",
                        "recovery_week",
                        "status",
                        "notes",
                    ],
                    "properties": {
                        "week_number": {
                            "type": "integer",
                            "minimum": 1,
                        },
                        "start_date": {
                            "type": "string",
                            "format": "date",
                        },
                        "end_date": {
                            "type": "string",
                            "format": "date",
                        },
                        "phase": {
                            "type": "string",
                            "enum": phase_types,
                        },
                        "target_load": _nullable_number(),
                        "load_min": _nullable_number(),
                        "load_max": _nullable_number(),
                        "target_duration_minutes": {
                            "type": [
                                "integer",
                                "null",
                            ],
                        },
                        "target_distance_km": _nullable_number(),
                        "target_elevation_gain_m": _nullable_number(),
                        "primary_stimuli": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "required": [
                                    "stimulus_type",
                                    "priority",
                                    "target_exposure_minutes",
                                    "notes",
                                ],
                                "properties": {
                                    "stimulus_type": {
                                        "type": "string",
                                        "enum": stimulus_types,
                                    },
                                    "priority": {
                                        "type": "string",
                                        "enum": [
                                            "low",
                                            "medium",
                                            "high",
                                        ],
                                    },
                                    "target_exposure_minutes": {
                                        "type": [
                                            "integer",
                                            "null",
                                        ],
                                    },
                                    "notes": {
                                        "type": [
                                            "string",
                                            "null",
                                        ],
                                    },
                                },
                            },
                        },
                        "recovery_week": {
                            "type": "boolean",
                        },
                        "status": {
                            "type": "string",
                            "enum": [
                                "planned",
                                "active",
                                "completed",
                                "revised",
                            ],
                        },
                        "notes": {
                            "type": [
                                "string",
                                "null",
                            ],
                        },
                    },
                },
            },
            "revision_changes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "action",
                        "target",
                        "description",
                        "reason",
                    ],
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": [
                                "keep",
                                "modify",
                                "add",
                                "remove",
                            ],
                        },
                        "target": {
                            "type": "string",
                            "minLength": 1,
                        },
                        "description": {
                            "type": "string",
                            "minLength": 1,
                        },
                        "reason": {
                            "type": "string",
                            "minLength": 1,
                        },
                    },
                },
            },
        },
    }


def _nullable_number() -> dict[str, object]:
    return {
        "type": [
            "number",
            "null",
        ],
    }
