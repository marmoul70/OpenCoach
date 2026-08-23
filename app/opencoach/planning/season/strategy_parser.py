from datetime import date
from typing import Any

from opencoach.planning.season.strategist_port import (
    SeasonStrategistInvalidResponseError,
)
from opencoach.planning.season.strategy import (
    MacrocyclePhase,
    TrainingStimulus,
    WeekTrajectory,
)
from opencoach.planning.season.strategy_proposal import (
    SeasonStrategyProposal,
    StrategyAssumption,
    StrategyDecision,
    StrategyFactReference,
    StrategyRevisionChange,
    StrategyUncertainty,
)


_PHASE_TYPES = {
    "foundation",
    "base",
    "build",
    "specific",
    "taper",
    "recovery",
    "race",
}

_STIMULUS_TYPES = {
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
}

_PRIORITIES = {
    "low",
    "medium",
    "high",
}

_TRAJECTORY_STATUSES = {
    "planned",
    "active",
    "completed",
    "revised",
}

_DECISION_TYPES = {
    "phase_structure",
    "load_progression",
    "recovery_strategy",
    "specificity_progression",
    "taper_strategy",
    "race_integration",
    "assessment_strategy",
    "other",
}

_CHANGE_ACTIONS = {
    "keep",
    "modify",
    "add",
    "remove",
}


def parse_season_strategy_proposal(
    payload: object,
) -> SeasonStrategyProposal:
    """Convertit strictement une réponse IA en proposition métier."""

    data = _expect_object(
        payload,
        "proposal",
    )

    _expect_exact_keys(
        data,
        {
            "summary",
            "facts_used",
            "assumptions",
            "decisions",
            "uncertainties",
            "phases",
            "weeks",
            "revision_changes",
        },
        "proposal",
    )

    try:
        return SeasonStrategyProposal(
            summary=_expect_string(
                data["summary"],
                "summary",
            ),
            facts_used=tuple(
                _parse_fact(item)
                for item in _expect_list(
                    data["facts_used"],
                    "facts_used",
                )
            ),
            assumptions=tuple(
                _parse_assumption(item)
                for item in _expect_list(
                    data["assumptions"],
                    "assumptions",
                )
            ),
            decisions=tuple(
                _parse_decision(item)
                for item in _expect_list(
                    data["decisions"],
                    "decisions",
                )
            ),
            uncertainties=tuple(
                _parse_uncertainty(item)
                for item in _expect_list(
                    data["uncertainties"],
                    "uncertainties",
                )
            ),
            phases=tuple(
                _parse_phase(item)
                for item in _expect_list(
                    data["phases"],
                    "phases",
                )
            ),
            weeks=tuple(
                _parse_week(item)
                for item in _expect_list(
                    data["weeks"],
                    "weeks",
                )
            ),
            revision_changes=tuple(
                _parse_revision_change(item)
                for item in _expect_list(
                    data["revision_changes"],
                    "revision_changes",
                )
            ),
        )
    except SeasonStrategistInvalidResponseError:
        raise
    except (
        TypeError,
        ValueError,
        KeyError,
    ) as exc:
        raise SeasonStrategistInvalidResponseError(
            "La proposition stratégique viole le contrat métier."
        ) from exc


def _parse_fact(
    payload: object,
) -> StrategyFactReference:
    data = _expect_object(
        payload,
        "fact",
    )

    _expect_exact_keys(
        data,
        {
            "source_path",
            "purpose",
        },
        "fact",
    )

    return StrategyFactReference(
        source_path=_expect_string(
            data["source_path"],
            "fact.source_path",
        ),
        purpose=_expect_string(
            data["purpose"],
            "fact.purpose",
        ),
    )


def _parse_assumption(
    payload: object,
) -> StrategyAssumption:
    data = _expect_object(
        payload,
        "assumption",
    )

    _expect_exact_keys(
        data,
        {
            "assumption_id",
            "description",
            "impact",
            "affected_area",
        },
        "assumption",
    )

    impact = _expect_enum(
        data["impact"],
        _PRIORITIES,
        "assumption.impact",
    )

    return StrategyAssumption(
        assumption_id=_expect_string(
            data["assumption_id"],
            "assumption.assumption_id",
        ),
        description=_expect_string(
            data["description"],
            "assumption.description",
        ),
        impact=impact,
        affected_area=_expect_string(
            data["affected_area"],
            "assumption.affected_area",
        ),
    )


def _parse_decision(
    payload: object,
) -> StrategyDecision:
    data = _expect_object(
        payload,
        "decision",
    )

    _expect_exact_keys(
        data,
        {
            "decision_type",
            "description",
            "rationale",
            "based_on_facts",
            "based_on_assumptions",
        },
        "decision",
    )

    return StrategyDecision(
        decision_type=_expect_enum(
            data["decision_type"],
            _DECISION_TYPES,
            "decision.decision_type",
        ),
        description=_expect_string(
            data["description"],
            "decision.description",
        ),
        rationale=_expect_string(
            data["rationale"],
            "decision.rationale",
        ),
        based_on_facts=_parse_string_tuple(
            data["based_on_facts"],
            "decision.based_on_facts",
        ),
        based_on_assumptions=_parse_string_tuple(
            data["based_on_assumptions"],
            "decision.based_on_assumptions",
        ),
    )


def _parse_uncertainty(
    payload: object,
) -> StrategyUncertainty:
    data = _expect_object(
        payload,
        "uncertainty",
    )

    _expect_exact_keys(
        data,
        {
            "level",
            "description",
            "affected_area",
            "resolution_hint",
        },
        "uncertainty",
    )

    return StrategyUncertainty(
        level=_expect_enum(
            data["level"],
            _PRIORITIES,
            "uncertainty.level",
        ),
        description=_expect_string(
            data["description"],
            "uncertainty.description",
        ),
        affected_area=_expect_string(
            data["affected_area"],
            "uncertainty.affected_area",
        ),
        resolution_hint=_expect_optional_string(
            data["resolution_hint"],
            "uncertainty.resolution_hint",
        ),
    )


def _parse_phase(
    payload: object,
) -> MacrocyclePhase:
    data = _expect_object(
        payload,
        "phase",
    )

    _expect_exact_keys(
        data,
        {
            "phase_type",
            "start_date",
            "end_date",
            "objective",
            "primary_stimuli",
        },
        "phase",
    )

    return MacrocyclePhase(
        phase_type=_expect_enum(
            data["phase_type"],
            _PHASE_TYPES,
            "phase.phase_type",
        ),
        start_date=_expect_date(
            data["start_date"],
            "phase.start_date",
        ),
        end_date=_expect_date(
            data["end_date"],
            "phase.end_date",
        ),
        objective=_expect_string(
            data["objective"],
            "phase.objective",
        ),
        primary_stimuli=tuple(
            _expect_enum(
                item,
                _STIMULUS_TYPES,
                "phase.primary_stimuli",
            )
            for item in _expect_list(
                data["primary_stimuli"],
                "phase.primary_stimuli",
            )
        ),
    )


def _parse_week(
    payload: object,
) -> WeekTrajectory:
    data = _expect_object(
        payload,
        "week",
    )

    _expect_exact_keys(
        data,
        {
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
        },
        "week",
    )

    week_number = _expect_integer(
        data["week_number"],
        "week.week_number",
    )

    if week_number < 1:
        raise SeasonStrategistInvalidResponseError(
            "week.week_number doit être supérieur ou égal à 1."
        )

    return WeekTrajectory(
        week_number=week_number,
        start_date=_expect_date(
            data["start_date"],
            "week.start_date",
        ),
        end_date=_expect_date(
            data["end_date"],
            "week.end_date",
        ),
        phase=_expect_enum(
            data["phase"],
            _PHASE_TYPES,
            "week.phase",
        ),
        target_load=_expect_optional_number(
            data["target_load"],
            "week.target_load",
        ),
        load_min=_expect_optional_number(
            data["load_min"],
            "week.load_min",
        ),
        load_max=_expect_optional_number(
            data["load_max"],
            "week.load_max",
        ),
        target_duration_minutes=_expect_optional_integer(
            data["target_duration_minutes"],
            "week.target_duration_minutes",
        ),
        target_distance_km=_expect_optional_number(
            data["target_distance_km"],
            "week.target_distance_km",
        ),
        target_elevation_gain_m=_expect_optional_number(
            data["target_elevation_gain_m"],
            "week.target_elevation_gain_m",
        ),
        primary_stimuli=tuple(
            _parse_stimulus(item)
            for item in _expect_list(
                data["primary_stimuli"],
                "week.primary_stimuli",
            )
        ),
        recovery_week=_expect_bool(
            data["recovery_week"],
            "week.recovery_week",
        ),
        status=_expect_enum(
            data["status"],
            _TRAJECTORY_STATUSES,
            "week.status",
        ),
        notes=_expect_optional_string(
            data["notes"],
            "week.notes",
        ),
    )


def _parse_stimulus(
    payload: object,
) -> TrainingStimulus:
    data = _expect_object(
        payload,
        "stimulus",
    )

    _expect_exact_keys(
        data,
        {
            "stimulus_type",
            "priority",
            "target_exposure_minutes",
            "notes",
        },
        "stimulus",
    )

    return TrainingStimulus(
        stimulus_type=_expect_enum(
            data["stimulus_type"],
            _STIMULUS_TYPES,
            "stimulus.stimulus_type",
        ),
        priority=_expect_enum(
            data["priority"],
            _PRIORITIES,
            "stimulus.priority",
        ),
        target_exposure_minutes=_expect_optional_integer(
            data["target_exposure_minutes"],
            "stimulus.target_exposure_minutes",
        ),
        notes=_expect_optional_string(
            data["notes"],
            "stimulus.notes",
        ),
    )


def _parse_revision_change(
    payload: object,
) -> StrategyRevisionChange:
    data = _expect_object(
        payload,
        "revision_change",
    )

    _expect_exact_keys(
        data,
        {
            "action",
            "target",
            "description",
            "reason",
        },
        "revision_change",
    )

    return StrategyRevisionChange(
        action=_expect_enum(
            data["action"],
            _CHANGE_ACTIONS,
            "revision_change.action",
        ),
        target=_expect_string(
            data["target"],
            "revision_change.target",
        ),
        description=_expect_string(
            data["description"],
            "revision_change.description",
        ),
        reason=_expect_string(
            data["reason"],
            "revision_change.reason",
        ),
    )


def _expect_object(
    value: object,
    path: str,
) -> dict[str, Any]:
    if not isinstance(
        value,
        dict,
    ):
        raise SeasonStrategistInvalidResponseError(
            f"{path} doit être un objet JSON."
        )

    if not all(
        isinstance(key, str)
        for key in value
    ):
        raise SeasonStrategistInvalidResponseError(
            f"{path} contient une clé non textuelle."
        )

    return value


def _expect_list(
    value: object,
    path: str,
) -> list[object]:
    if not isinstance(
        value,
        list,
    ):
        raise SeasonStrategistInvalidResponseError(
            f"{path} doit être une liste."
        )

    return value


def _expect_exact_keys(
    value: dict[str, Any],
    expected: set[str],
    path: str,
) -> None:
    actual = set(
        value
    )

    missing = (
        expected - actual
    )

    extra = (
        actual - expected
    )

    if missing:
        raise SeasonStrategistInvalidResponseError(
            f"{path} ne contient pas tous les champs requis: "
            f"{', '.join(sorted(missing))}."
        )

    if extra:
        raise SeasonStrategistInvalidResponseError(
            f"{path} contient des champs inconnus: "
            f"{', '.join(sorted(extra))}."
        )


def _expect_string(
    value: object,
    path: str,
) -> str:
    if (
        not isinstance(
            value,
            str,
        )
        or not value.strip()
    ):
        raise SeasonStrategistInvalidResponseError(
            f"{path} doit être une chaîne non vide."
        )

    return value


def _expect_optional_string(
    value: object,
    path: str,
) -> str | None:
    if value is None:
        return None

    if not isinstance(
        value,
        str,
    ):
        raise SeasonStrategistInvalidResponseError(
            f"{path} doit être une chaîne ou null."
        )

    return value


def _expect_integer(
    value: object,
    path: str,
) -> int:
    if (
        isinstance(
            value,
            bool,
        )
        or not isinstance(
            value,
            int,
        )
    ):
        raise SeasonStrategistInvalidResponseError(
            f"{path} doit être un entier."
        )

    return value


def _expect_optional_integer(
    value: object,
    path: str,
) -> int | None:
    if value is None:
        return None

    return _expect_integer(
        value,
        path,
    )


def _expect_optional_number(
    value: object,
    path: str,
) -> float | None:
    if value is None:
        return None

    if (
        isinstance(
            value,
            bool,
        )
        or not isinstance(
            value,
            (
                int,
                float,
            ),
        )
    ):
        raise SeasonStrategistInvalidResponseError(
            f"{path} doit être un nombre ou null."
        )

    return float(
        value
    )


def _expect_bool(
    value: object,
    path: str,
) -> bool:
    if not isinstance(
        value,
        bool,
    ):
        raise SeasonStrategistInvalidResponseError(
            f"{path} doit être un booléen."
        )

    return value


def _expect_enum(
    value: object,
    values: set[str],
    path: str,
) -> str:
    text = _expect_string(
        value,
        path,
    )

    if text not in values:
        raise SeasonStrategistInvalidResponseError(
            f"{path} contient une valeur inconnue: {text}."
        )

    return text


def _expect_date(
    value: object,
    path: str,
) -> date:
    text = _expect_string(
        value,
        path,
    )

    try:
        return date.fromisoformat(
            text
        )
    except ValueError as exc:
        raise SeasonStrategistInvalidResponseError(
            f"{path} doit être une date ISO valide."
        ) from exc


def _parse_string_tuple(
    value: object,
    path: str,
) -> tuple[str, ...]:
    return tuple(
        _expect_string(
            item,
            path,
        )
        for item in _expect_list(
            value,
            path,
        )
    )
