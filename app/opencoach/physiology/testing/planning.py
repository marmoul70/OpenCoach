"""Intégration des tests physiologiques au planning hebdomadaire.

Principe fondamental :

- un test ne crée jamais une séance supplémentaire ;
- il cible une séance qualitative existante ;
- la séance n'est remplacée que si l'athlète accepte ;
- en cas de refus, l'intention d'entraînement initiale est conservée.

Ce module reste déterministe et ne persiste rien.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from opencoach.physiology.testing.proposal import (
    PhysiologicalTestDecision,
    PhysiologicalTestProposal,
    PhysiologicalTestReplacementStimulus,
)
from opencoach.planning.sessions.intent import (
    SessionIntent,
)
from opencoach.planning.stimulus.training import (
    StimulusLoadCategory,
    TrainingStimulus,
    stimulus_load_category,
)


class PhysiologicalTestPlanningStatus(StrEnum):
    """Résultat de l'intégration d'une proposition."""

    NO_COMPATIBLE_SESSION = (
        "no_compatible_session"
    )

    AWAITING_ATHLETE = (
        "awaiting_athlete"
    )

    TEST_REPLACES_SESSION = (
        "test_replaces_session"
    )

    ORIGINAL_SESSION_KEPT = (
        "original_session_kept"
    )


@dataclass(
    frozen=True,
    slots=True,
)
class PhysiologicalTestSessionTarget:
    """Séance qualitative ciblée par un test."""

    intent_index: int

    intent: SessionIntent

    compatibility_score: int


@dataclass(
    frozen=True,
    slots=True,
)
class PhysiologicalTestPlanningDecision:
    """Décision de placement d'une proposition de test."""

    status: PhysiologicalTestPlanningStatus

    proposal: PhysiologicalTestProposal

    target: (
        PhysiologicalTestSessionTarget
        | None
    )

    reason: str

    @property
    def session_count_delta(
        self,
    ) -> int:
        """Un test ne doit jamais augmenter le nombre de séances."""

        return 0

    @property
    def test_should_replace_session(
        self,
    ) -> bool:
        return (
            self.status
            is PhysiologicalTestPlanningStatus
            .TEST_REPLACES_SESSION
        )

    @property
    def original_session_should_remain(
        self,
    ) -> bool:
        return (
            self.status
            in {
                PhysiologicalTestPlanningStatus
                .AWAITING_ATHLETE,

                PhysiologicalTestPlanningStatus
                .ORIGINAL_SESSION_KEPT,
            }
        )


def plan_physiological_test_in_week(
    *,
    proposal: PhysiologicalTestProposal,
    intents: tuple[
        SessionIntent,
        ...,
    ],
) -> PhysiologicalTestPlanningDecision:
    """Associe un test à une séance existante.

    Le moteur recherche d'abord une séance qualitative
    compatible avec le stimulus de remplacement du test.

    La décision de l'athlète détermine ensuite si le test
    remplace réellement cette séance.
    """

    target = (
        select_test_target_session(
            proposal=proposal,
            intents=intents,
        )
    )

    if target is None:
        return PhysiologicalTestPlanningDecision(
            status=(
                PhysiologicalTestPlanningStatus
                .NO_COMPATIBLE_SESSION
            ),
            proposal=proposal,
            target=None,
            reason=(
                "Aucune séance qualitative compatible "
                "n'est disponible cette semaine. "
                "Le test ne doit pas être ajouté comme "
                "séance supplémentaire."
            ),
        )

    if (
        proposal.decision
        is PhysiologicalTestDecision.PENDING
    ):
        return PhysiologicalTestPlanningDecision(
            status=(
                PhysiologicalTestPlanningStatus
                .AWAITING_ATHLETE
            ),
            proposal=proposal,
            target=target,
            reason=(
                "Le test peut remplacer une séance "
                "qualitative, mais OpenCoach attend "
                "la décision de l'athlète."
            ),
        )

    if (
        proposal.decision
        is PhysiologicalTestDecision.DECLINED
    ):
        return PhysiologicalTestPlanningDecision(
            status=(
                PhysiologicalTestPlanningStatus
                .ORIGINAL_SESSION_KEPT
            ),
            proposal=proposal,
            target=target,
            reason=(
                "L'athlète a refusé le test. "
                "La séance qualitative prévue est "
                "conservée."
            ),
        )

    return PhysiologicalTestPlanningDecision(
        status=(
            PhysiologicalTestPlanningStatus
            .TEST_REPLACES_SESSION
        ),
        proposal=proposal,
        target=target,
        reason=(
            "L'athlète a accepté le test. "
            "Le test remplace la séance qualitative "
            "sélectionnée sans augmenter le nombre "
            "de séances de la semaine."
        ),
    )


def select_test_target_session(
    *,
    proposal: PhysiologicalTestProposal,
    intents: tuple[
        SessionIntent,
        ...,
    ],
) -> PhysiologicalTestSessionTarget | None:
    """Sélectionne la meilleure séance à remplacer."""

    candidates: list[
        PhysiologicalTestSessionTarget
    ] = []

    for index, intent in enumerate(
        intents
    ):
        score = (
            _compatibility_score(
                replacement_stimulus=(
                    proposal
                    .replacement_stimulus
                ),
                intent=intent,
            )
        )

        if score <= 0:
            continue

        candidates.append(
            PhysiologicalTestSessionTarget(
                intent_index=index,
                intent=intent,
                compatibility_score=score,
            )
        )

    if not candidates:
        return None

    return max(
        candidates,
        key=lambda candidate: (
            candidate.compatibility_score,
            _importance_score(
                candidate.intent
            ),
            -candidate.intent_index,
        ),
    )


def _compatibility_score(
    *,
    replacement_stimulus: (
        PhysiologicalTestReplacementStimulus
    ),
    intent: SessionIntent,
) -> int:
    """Évalue si le test peut remplacer cette intention."""

    primary = (
        intent.primary_stimulus
    )

    if (
        stimulus_load_category(
            primary
        )
        is not StimulusLoadCategory.QUALITY
    ):
        return 0

    compatible = (
        _replacement_training_stimuli(
            replacement_stimulus
        )
    )

    if primary in compatible:
        return 100

    if any(
        stimulus in compatible
        for stimulus
        in intent.secondary_stimuli
    ):
        return 80

    # Une séance qualité différente reste un dernier
    # recours, mais n'est pas la cible privilégiée.
    return 20


def _replacement_training_stimuli(
    replacement: (
        PhysiologicalTestReplacementStimulus
    ),
) -> tuple[
    TrainingStimulus,
    ...,
]:
    """Traduit le besoin de remplacement vers le domaine planning."""

    if (
        replacement
        is PhysiologicalTestReplacementStimulus
        .AEROBIC_POWER
    ):
        return (
            TrainingStimulus.VO2MAX,
            TrainingStimulus.SPEED_DEVELOPMENT,
        )

    if (
        replacement
        is PhysiologicalTestReplacementStimulus
        .THRESHOLD
    ):
        return (
            TrainingStimulus.THRESHOLD,
        )

    if (
        replacement
        is PhysiologicalTestReplacementStimulus
        .UPHILL_INTENSITY
    ):
        return (
            TrainingStimulus.UPHILL_THRESHOLD,
            TrainingStimulus.UPHILL_STRENGTH_ENDURANCE,
            TrainingStimulus.UPHILL_STRENGTH,
        )

    if (
        replacement
        is PhysiologicalTestReplacementStimulus
        .LONG_TRAIL_QUALITY
    ):
        return (
            TrainingStimulus.RACE_SPECIFIC,
            TrainingStimulus.UPHILL_STRENGTH_ENDURANCE,
        )

    return ()


def _importance_score(
    intent: SessionIntent,
) -> int:
    """Départage deux séances également compatibles."""

    value = (
        intent.importance.value
    )

    if value == "key":
        return 3

    if value == "important":
        return 2

    return 1
