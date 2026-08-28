"""Création automatique des propositions de tests physiologiques.

Ce service intervient après la génération d'une semaine.

Il ne modifie aucune séance.

Il peut uniquement :
- déterminer si une calibration mérite d'être proposée ;
- sélectionner une séance qualité déjà persistée ;
- créer une proposition PENDING rattachée à cette séance.

La décision finale reste toujours celle de l'athlète.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from uuid import UUID

from opencoach.database.repositories.physiological_measurement import (
    PhysiologicalMeasurementRepository,
)
from opencoach.database.repositories.physiological_test_proposal import (
    PhysiologicalTestProposalRepository,
)
from opencoach.database.repositories.training_session import (
    TrainingSessionRepository,
)
from opencoach.models import (
    PhysiologicalMeasurement,
    TrainingSession,
)
from opencoach.physiology.testing.decision import (
    DECLINED_TEST_COOLDOWN_DAYS,
    PhysiologicalTestNeedRequest,
    PreviousTestDecision,
    PhysiologicalTestingSeasonPhase,
    evaluate_physiological_test_need,
)
from opencoach.physiology.testing.freshness import (
    MeasurementConfidence,
    PhysiologicalMeasurementEvidence,
)
from opencoach.physiology.testing.models import (
    PhysiologicalMetric,
    PhysiologicalTestAcquisitionMode,
    PhysiologicalTestType,
    SportDiscipline,
)
from opencoach.physiology.testing.proposal import (
    PhysiologicalTestDecision,
    PhysiologicalTestProposal,
)
from opencoach.physiology.testing.proposal_service import (
    PhysiologicalTestProposalRequest,
    propose_physiological_test,
)
from opencoach.planning.weekly.training_envelope import (
    TrainingPhase,
)


@dataclass(
    frozen=True,
    slots=True,
)
class AutomaticPhysiologicalTestProposalRequest:
    """Contexte d'évaluation d'une semaine générée."""

    athlete_profile_id: UUID

    reference_date: date

    week_start: date
    week_end: date

    phase: TrainingPhase

    disciplines: tuple[
        SportDiscipline,
        ...,
    ]


@dataclass(
    frozen=True,
    slots=True,
)
class AutomaticPhysiologicalTestProposalResult:
    """Résultat de l'évaluation automatique."""

    proposal: (
        PhysiologicalTestProposal
        | None
    )

    reason: str

    @property
    def created(
        self,
    ) -> bool:
        return self.proposal is not None


class AutomaticPhysiologicalTestProposalService:
    """Décide et persiste une proposition de test."""

    def __init__(
        self,
        *,
        measurement_repository: (
            PhysiologicalMeasurementRepository
        ),
        proposal_repository: (
            PhysiologicalTestProposalRepository
        ),
        training_session_repository: (
            TrainingSessionRepository
        ),
    ) -> None:
        self.measurement_repository = (
            measurement_repository
        )

        self.proposal_repository = (
            proposal_repository
        )

        self.training_session_repository = (
            training_session_repository
        )

    def evaluate_week(
        self,
        request: AutomaticPhysiologicalTestProposalRequest,
    ) -> AutomaticPhysiologicalTestProposalResult:
        """Évalue la VMA et crée au besoin une proposition.

        PT0.7a limite volontairement l'automatisation à la VMA.
        Les autres métriques seront ajoutées lorsque ce premier
        workflow sera validé de bout en bout.
        """

        metric = (
            PhysiologicalMetric.VMA
        )

        # ----------------------------------------------------
        # Une seule proposition en attente à la fois.
        # ----------------------------------------------------

        pending = (
            self.proposal_repository
            .get_pending(
                request.athlete_profile_id
            )
        )

        if pending:
            return (
                AutomaticPhysiologicalTestProposalResult(
                    proposal=None,
                    reason=(
                        "Une proposition de test attend déjà "
                        "la décision de l'athlète."
                    ),
                )
            )

        # ----------------------------------------------------
        # Dernière VMA connue.
        # ----------------------------------------------------

        measurement = (
            self.measurement_repository
            .get_latest_measurement(
                request.athlete_profile_id,
                "vma",
            )
        )

        evidence = (
            _measurement_to_evidence(
                measurement
            )
        )

        # ----------------------------------------------------
        # Respect d'un refus récent.
        # ----------------------------------------------------

        previous_decision = (
            _latest_recent_decision(
                athlete_profile_id=(
                    request.athlete_profile_id
                ),
                reference_date=(
                    request.reference_date
                ),
                repository=(
                    self.proposal_repository
                ),
            )
        )

        need = (
            evaluate_physiological_test_need(
                PhysiologicalTestNeedRequest(
                    metric=metric,
                    reference_date=(
                        request.reference_date
                    ),
                    disciplines=(
                        request.disciplines
                    ),
                    season_phase=(
                        _map_training_phase(
                            request.phase
                        )
                    ),
                    measurement=evidence,
                    previous_test_decision=(
                        previous_decision
                    ),
                )
            )
        )

        if not need.should_propose:
            return (
                AutomaticPhysiologicalTestProposalResult(
                    proposal=None,
                    reason=need.reason,
                )
            )

        if (
            need.preferred_protocol
            is not PhysiologicalTestType.HALF_COOPER
        ):
            return (
                AutomaticPhysiologicalTestProposalResult(
                    proposal=None,
                    reason=(
                        "PT0.7a automatise uniquement "
                        "le Demi-Cooper pour la VMA."
                    ),
                )
            )

        # ----------------------------------------------------
        # Séances réellement présentes dans la semaine.
        # ----------------------------------------------------

        sessions = (
            self.training_session_repository
            .list_sessions_between(
                request.athlete_profile_id,
                request.week_start,
                request.week_end,
            )
        )

        target = (
            _select_vma_target_session(
                sessions
            )
        )

        if target is None:
            return (
                AutomaticPhysiologicalTestProposalResult(
                    proposal=None,
                    reason=(
                        "Aucune séance de puissance aérobie "
                        "compatible n'est prévue cette semaine. "
                        "OpenCoach attend une meilleure fenêtre."
                    ),
                )
            )

        # ----------------------------------------------------
        # Construction de la proposition.
        # ----------------------------------------------------

        proposal = (
            propose_physiological_test(
                PhysiologicalTestProposalRequest(
                    athlete_profile_id=(
                        request.athlete_profile_id
                    ),
                    protocol=(
                        PhysiologicalTestType
                        .HALF_COOPER
                    ),
                    proposed_date=(
                        target.date
                    ),
                    reason=need.reason,
                )
            )
            .assign_to_session(
                _require_session_id(
                    target
                )
            )
        )

        saved = (
            self.proposal_repository
            .save(
                proposal
            )
        )

        return (
            AutomaticPhysiologicalTestProposalResult(
                proposal=saved,
                reason=(
                    "OpenCoach propose un Demi-Cooper "
                    "à la place d'une séance de puissance "
                    "aérobie déjà prévue."
                ),
            )
        )


def _measurement_to_evidence(
    measurement: PhysiologicalMeasurement | None,
) -> PhysiologicalMeasurementEvidence | None:
    """Adapte la mesure historique au moteur de fraîcheur."""

    if measurement is None:
        return None

    confidence = {
        "low": MeasurementConfidence.LOW,
        "medium": MeasurementConfidence.MEDIUM,
        "high": MeasurementConfidence.HIGH,
    }.get(
        measurement.confidence,
        MeasurementConfidence.MEDIUM,
    )

    acquisition_mode = (
        PhysiologicalTestAcquisitionMode.MANUAL
        if measurement.source == "manual"
        else PhysiologicalTestAcquisitionMode.PASSIVE
    )

    protocol = None

    if measurement.protocol:
        try:
            protocol = (
                PhysiologicalTestType(
                    measurement.protocol
                )
            )
        except ValueError:
            protocol = None

    return PhysiologicalMeasurementEvidence(
        metric=PhysiologicalMetric.VMA,
        measured_at=measurement.measured_at,
        confidence=confidence,
        acquisition_mode=acquisition_mode,
        protocol=protocol,
    )


def _latest_recent_decision(
    *,
    athlete_profile_id: UUID,
    reference_date: date,
    repository: PhysiologicalTestProposalRepository,
) -> PreviousTestDecision | None:
    """Retourne la décision de test la plus récente."""

    since = (
        reference_date
        - timedelta(
            days=(
                DECLINED_TEST_COOLDOWN_DAYS
                + 1
            )
        )
    )

    history = repository.list_since(
        athlete_profile_id,
        since,
    )

    decided = tuple(
        proposal
        for proposal in history
        if (
            proposal.decision
            is not PhysiologicalTestDecision.PENDING
        )
    )

    if not decided:
        return None

    latest = max(
        decided,
        key=lambda proposal: (
            proposal.proposed_date
        ),
    )

    return PreviousTestDecision(
        protocol=latest.protocol,
        decision=latest.decision,
        decided_at=(
            latest.proposed_date
        ),
    )


def _select_vma_target_session(
    sessions: list[
        TrainingSession
    ],
) -> TrainingSession | None:
    """Choisit une séance qualité compatible avec un test VMA.

    Une vraie séance VO2max est prioritaire.
    Une séance de développement de vitesse constitue
    la seconde possibilité.

    Aucune séance facile, seuil ou sortie longue n'est
    sacrifiée dans PT0.7a.
    """

    eligible = tuple(
        session
        for session in sessions
        if (
            session.status == "planned"
            and session.activity_id is None
            and session.type
            in {
                "vo2max",
                "speed_development",
            }
        )
    )

    if not eligible:
        return None

    priority = {
        "vo2max": 2,
        "speed_development": 1,
    }

    return max(
        eligible,
        key=lambda session: (
            priority.get(
                session.type,
                0,
            ),
            -session.date.toordinal(),
        ),
    )


def _map_training_phase(
    phase: TrainingPhase,
) -> PhysiologicalTestingSeasonPhase:
    """Adapte la vraie phase OpenCoach au moteur de tests."""

    mapping = {
        TrainingPhase.FOUNDATION: (
            PhysiologicalTestingSeasonPhase.BASE
        ),
        TrainingPhase.BASE: (
            PhysiologicalTestingSeasonPhase.BASE
        ),
        TrainingPhase.BUILD: (
            PhysiologicalTestingSeasonPhase.BUILD
        ),
        TrainingPhase.SPECIFIC: (
            PhysiologicalTestingSeasonPhase.SPECIFIC
        ),
        TrainingPhase.TAPER: (
            PhysiologicalTestingSeasonPhase.TAPER
        ),
        TrainingPhase.RECOVERY: (
            PhysiologicalTestingSeasonPhase.RECOVERY
        ),
        TrainingPhase.RETURN_TO_TRAINING: (
            PhysiologicalTestingSeasonPhase
            .RETURN_TO_TRAINING
        ),
    }

    return mapping[
        phase
    ]


def _require_session_id(
    session: TrainingSession,
) -> UUID:
    if session.id is None:
        raise RuntimeError(
            "Une séance persistée doit posséder "
            "un identifiant."
        )

    return session.id
