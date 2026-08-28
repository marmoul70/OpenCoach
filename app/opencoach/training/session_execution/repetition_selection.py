"""Sélection des répétitions réellement prouvées."""

from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass

from opencoach.models import ActivityDetail

from .interval_prescription import (
    IntervalSetPrescription,
)
from .repetition_evidence import (
    RepetitionEvidence,
    RepetitionEvidenceScorer,
)
from .repetition_transition import (
    score_repetition_transition,
)
from .stream_repetition_detection import (
    StreamRepetitionCandidate,
    build_distance_repetition_candidates,
)


DEFAULT_MINIMUM_CONFIDENCE = 0.62
DEFAULT_MINIMUM_SUPPORT_SCORE = 0.35


@dataclass(frozen=True, slots=True)
class EvidencedRepetitionCandidate:
    """Candidat accompagné de ses preuves physiologiques."""

    candidate: StreamRepetitionCandidate
    evidence: RepetitionEvidence


def select_evidenced_distance_repetitions(
    activity_detail: ActivityDetail,
    prescription: IntervalSetPrescription,
    *,
    minimum_confidence: float = (
        DEFAULT_MINIMUM_CONFIDENCE
    ),
    minimum_support_score: float = (
        DEFAULT_MINIMUM_SUPPORT_SCORE
    ),
) -> tuple[
    EvidencedRepetitionCandidate,
    ...,
]:
    """Sélectionne jusqu'au nombre de répétitions prescrit.

    Le nombre prescrit constitue un plafond et non un objectif
    à atteindre artificiellement.
    """

    if not (
        0.0 <= minimum_confidence <= 1.0
    ):
        raise ValueError(
            "minimum_confidence doit être compris "
            "entre 0 et 1."
        )

    if not (
        0.0 <= minimum_support_score <= 1.0
    ):
        raise ValueError(
            "minimum_support_score doit être compris "
            "entre 0 et 1."
        )

    raw_candidates = (
        build_distance_repetition_candidates(
            activity_detail,
            prescription,
        )
    )

    evidenced = []

    scorer = RepetitionEvidenceScorer(
        activity_detail,
        prescription,
    )

    for candidate in raw_candidates:
        evidence = scorer.score(
            candidate
        )

        if not _is_supported(
            evidence,
            minimum_confidence=minimum_confidence,
            minimum_support_score=(
                minimum_support_score
            ),
        ):
            continue

        evidenced.append(
            EvidencedRepetitionCandidate(
                candidate=candidate,
                evidence=evidence,
            )
        )

    if not evidenced:
        return ()

    minimum_gap = _minimum_gap(
        prescription
    )

    ordered = tuple(
        sorted(
            evidenced,
            key=lambda item: (
                item.candidate.start_time_seconds,
                item.candidate.end_time_seconds,
                -item.evidence.confidence,
            ),
        )
    )

    indexes = _select_best_combination(
        ordered,
        maximum_count=(
            prescription.repetitions
        ),
        minimum_gap_seconds=minimum_gap,
        prescription=prescription,
    )

    return tuple(
        ordered[index]
        for index in indexes
    )


def _is_supported(
    evidence: RepetitionEvidence,
    *,
    minimum_confidence: float,
    minimum_support_score: float,
) -> bool:
    if (
        evidence.confidence
        < minimum_confidence
    ):
        return False

    # Une durée/allure correcte seule n'est pas suffisante.
    # Il faut au moins un signal dynamique qui confirme
    # l'alternance travail/récupération.
    supporting_scores = tuple(
        value
        for value in (
            evidence.speed_contrast_score,
            evidence.cadence_score,
            evidence.watts_score,
            evidence.heart_rate_score,
        )
        if value is not None
    )

    if not supporting_scores:
        return False

    return (
        max(supporting_scores)
        >= minimum_support_score
    )


def _minimum_gap(
    prescription: IntervalSetPrescription,
) -> float:
    recovery = (
        prescription.recovery_duration_seconds
    )

    if recovery is None:
        return 1.0

    # Le but est seulement d'empêcher plusieurs fenêtres
    # glissantes issues de la même fraction.
    return max(
        1.0,
        recovery * 0.30,
    )


def _select_best_combination(
    candidates: tuple[
        EvidencedRepetitionCandidate,
        ...,
    ],
    *,
    maximum_count: int,
    minimum_gap_seconds: float,
    prescription: IntervalSetPrescription,
) -> tuple[int, ...]:
    """Choisit la meilleure séquence travail/récupération.

    La prescription guide désormais deux niveaux :

    1. chaque répétition :
       distance + durée/allure + preuves multi-signal ;

    2. chaque transition :
       récupération réellement observée comparée à la
       récupération prescrite.

    Le nombre de répétitions prescrit reste uniquement un plafond.
    """

    if (
        not candidates
        or maximum_count <= 0
    ):
        return ()

    ordered = tuple(
        sorted(
            enumerate(candidates),
            key=lambda item: (
                item[1].candidate.start_time_seconds,
                item[1].candidate.end_time_seconds,
                -item[1].evidence.confidence,
            ),
        )
    )

    original_indexes = tuple(
        item[0]
        for item in ordered
    )

    values = tuple(
        item[1]
        for item in ordered
    )

    count = len(values)

    maximum_count = min(
        maximum_count,
        count,
    )

    # dp[k][i] =
    # meilleure séquence de k répétitions se terminant par i.
    #
    # Valeur :
    # (
    #   score global,
    #   somme confidence individuelle,
    #   somme score récupération,
    #   tuple indexes
    # )
    dp: list[
        list[
            tuple[
                float,
                float,
                float,
                tuple[int, ...],
            ]
            | None
        ]
    ] = [
        [
            None
            for _ in range(count)
        ]
        for _ in range(
            maximum_count + 1
        )
    ]

    # Une répétition isolée ne possède pas encore de transition.
    for index, item in enumerate(values):
        confidence = (
            item.evidence.confidence
        )

        dp[1][index] = (
            confidence,
            confidence,
            0.0,
            (index,),
        )

    TRANSITION_WEIGHT = 0.45

    for selected_count in range(
        2,
        maximum_count + 1,
    ):
        for current_index in range(
            count
        ):
            current = values[
                current_index
            ]

            best = None

            for previous_index in range(
                current_index
            ):
                previous_state = dp[
                    selected_count - 1
                ][
                    previous_index
                ]

                if previous_state is None:
                    continue

                previous = values[
                    previous_index
                ]

                gap = (
                    current.candidate.start_time_seconds
                    - previous.candidate.end_time_seconds
                )

                if gap < minimum_gap_seconds:
                    continue

                transition = (
                    score_repetition_transition(
                        previous.candidate,
                        current.candidate,
                        # Toutes les répétitions de ce groupe
                        # partagent la même prescription.
                        prescription,
                    )
                )

                confidence_sum = (
                    previous_state[1]
                    + current.evidence.confidence
                )

                recovery_sum = (
                    previous_state[2]
                    + transition.recovery_score
                )

                # Score moyen permettant de comparer proprement
                # des séquences de même longueur.
                repetition_mean = (
                    confidence_sum
                    / selected_count
                )

                transition_mean = (
                    recovery_sum
                    / (
                        selected_count - 1
                    )
                )

                global_score = (
                    repetition_mean
                    + (
                        TRANSITION_WEIGHT
                        * transition_mean
                    )
                )

                state = (
                    global_score,
                    confidence_sum,
                    recovery_sum,
                    (
                        *previous_state[3],
                        current_index,
                    ),
                )

                if (
                    best is None
                    or _better_sequence(
                        state,
                        best,
                    )
                    is state
                ):
                    best = state

            dp[selected_count][
                current_index
            ] = best

    # On conserve en priorité le plus grand nombre de répétitions
    # réellement étayées. La cohérence de récupération choisit
    # ensuite la meilleure séquence parmi ces solutions.
    for selected_count in range(
        maximum_count,
        0,
        -1,
    ):
        states = [
            state
            for state in dp[selected_count]
            if state is not None
        ]

        if not states:
            continue

        best = states[0]

        for state in states[1:]:
            best = _better_sequence(
                state,
                best,
            )

        selected_ordered = best[3]

        selected_original = tuple(
            original_indexes[index]
            for index in selected_ordered
        )

        return tuple(
            sorted(
                selected_original,
                key=lambda index: (
                    candidates[index]
                    .candidate
                    .start_time_seconds
                ),
            )
        )

    return ()


def _better_sequence(
    left: tuple[
        float,
        float,
        float,
        tuple[int, ...],
    ],
    right: tuple[
        float,
        float,
        float,
        tuple[int, ...],
    ],
):
    if abs(
        left[0] - right[0]
    ) > 1e-9:
        return (
            left
            if left[0] > right[0]
            else right
        )

    if abs(
        left[1] - right[1]
    ) > 1e-9:
        return (
            left
            if left[1] > right[1]
            else right
        )

    if abs(
        left[2] - right[2]
    ) > 1e-9:
        return (
            left
            if left[2] > right[2]
            else right
        )

    return (
        left
        if left[3] < right[3]
        else right
    )

def _better(
    left,
    right,
):
    if left[0] != right[0]:
        return (
            left
            if left[0] > right[0]
            else right
        )

    if abs(
        left[1] - right[1]
    ) > 1e-9:
        return (
            left
            if left[1] > right[1]
            else right
        )

    return (
        left
        if left[2] < right[2]
        else right
    )
