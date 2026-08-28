"""Cohérence temporelle entre répétitions successives."""

from __future__ import annotations

from dataclasses import dataclass

from .interval_prescription import (
    IntervalSetPrescription,
)
from .stream_repetition_detection import (
    StreamRepetitionCandidate,
)


@dataclass(frozen=True, slots=True)
class RepetitionTransitionEvidence:
    """Preuve structurelle entre deux répétitions."""

    recovery_duration_seconds: float
    recovery_score: float

    @property
    def is_valid(self) -> bool:
        return (
            self.recovery_duration_seconds
            >= 0.0
        )


def score_repetition_transition(
    previous: StreamRepetitionCandidate,
    current: StreamRepetitionCandidate,
    prescription: IntervalSetPrescription,
) -> RepetitionTransitionEvidence:
    """Évalue la récupération séparant deux fractions.

    La récupération prescrite guide la recherche mais ne
    constitue pas un filtre absolu : une récupération mal
    exécutée reste observable et pourra être évaluée ensuite.
    """

    recovery = (
        current.start_time_seconds
        - previous.end_time_seconds
    )

    if recovery < 0:
        return RepetitionTransitionEvidence(
            recovery_duration_seconds=recovery,
            recovery_score=0.0,
        )

    expected = (
        prescription.recovery_duration_seconds
    )

    if expected is None:
        return RepetitionTransitionEvidence(
            recovery_duration_seconds=recovery,
            recovery_score=1.0,
        )

    if expected == 0:
        score = (
            1.0
            if recovery <= 1.0
            else max(
                0.0,
                1.0 - recovery / 30.0,
            )
        )

        return RepetitionTransitionEvidence(
            recovery_duration_seconds=recovery,
            recovery_score=round(
                score,
                4,
            ),
        )

    relative_error = (
        abs(
            recovery - expected
        )
        / expected
    )

    # Courbe volontairement progressive :
    #
    # récup exacte        -> 1.00
    # ±10 %               -> 0.90
    # ±20 %               -> 0.80
    # ±35 %               -> 0.65
    # ±50 %               -> 0.50
    # ±100 %              -> 0.00
    #
    # Elle sert à choisir la séquence la plus plausible,
    # pas à supprimer une fraction réellement exécutée.
    score = max(
        0.0,
        1.0 - relative_error,
    )

    return RepetitionTransitionEvidence(
        recovery_duration_seconds=round(
            recovery,
            3,
        ),
        recovery_score=round(
            score,
            4,
        ),
    )
