"""Repository SQLAlchemy des propositions de tests physiologiques."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import (
    select,
)
from sqlalchemy.exc import (
    SQLAlchemyError,
)
from sqlalchemy.orm import Session

from opencoach.database.models.physiological_test_proposal import (
    PhysiologicalTestProposal
    as PhysiologicalTestProposalModel,
)
from opencoach.database.repositories.physiological_test_proposal import (
    PhysiologicalTestProposalRepository,
    PhysiologicalTestProposalRepositoryError,
)
from opencoach.physiology.testing.models import (
    PhysiologicalMetric,
    PhysiologicalTestType,
)
from opencoach.physiology.testing.proposal import (
    PhysiologicalTestDecision,
    PhysiologicalTestProposal,
    PhysiologicalTestReplacementStimulus,
)


class SqlPhysiologicalTestProposalRepository(
    PhysiologicalTestProposalRepository
):
    """Persistance SQLAlchemy des propositions de tests."""

    def __init__(
        self,
        session: Session,
    ) -> None:
        self.session = session

    def save(
        self,
        proposal: PhysiologicalTestProposal,
    ) -> PhysiologicalTestProposal:
        try:
            database_proposal = None

            if proposal.id is not None:
                database_proposal = (
                    self.session.scalar(
                        select(
                            PhysiologicalTestProposalModel
                        ).where(
                            PhysiologicalTestProposalModel.id
                            == proposal.id,
                            PhysiologicalTestProposalModel
                            .athlete_profile_id
                            == proposal.athlete_profile_id,
                        )
                    )
                )

            if database_proposal is None:
                database_proposal = (
                    PhysiologicalTestProposalModel(
                        athlete_profile_id=(
                            proposal
                            .athlete_profile_id
                        ),
                    )
                )

                self.session.add(
                    database_proposal
                )

            database_proposal.target_session_id = (
                proposal.target_session_id
            )

            database_proposal.protocol = (
                proposal.protocol.value
            )

            database_proposal.target_metrics = [
                metric.value
                for metric
                in proposal.target_metrics
            ]

            database_proposal.proposed_date = (
                proposal.proposed_date
            )

            database_proposal.reason = (
                proposal.reason
            )

            database_proposal.recommendation = (
                proposal.recommendation
            )

            database_proposal.replacement_stimulus = (
                proposal
                .replacement_stimulus
                .value
            )

            database_proposal.decision = (
                proposal.decision.value
            )

            self.session.commit()

            self.session.refresh(
                database_proposal
            )

            return self._to_domain(
                database_proposal
            )

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise (
                PhysiologicalTestProposalRepositoryError(
                    "Impossible d'enregistrer "
                    "la proposition de test."
                )
            ) from exc

    def get(
        self,
        athlete_profile_id: UUID,
        proposal_id: UUID,
    ) -> PhysiologicalTestProposal | None:
        try:
            database_proposal = (
                self.session.scalar(
                    select(
                        PhysiologicalTestProposalModel
                    ).where(
                        PhysiologicalTestProposalModel
                        .athlete_profile_id
                        == athlete_profile_id,
                        PhysiologicalTestProposalModel.id
                        == proposal_id,
                    )
                )
            )

            if database_proposal is None:
                return None

            return self._to_domain(
                database_proposal
            )

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise (
                PhysiologicalTestProposalRepositoryError(
                    "Impossible de charger "
                    "la proposition de test."
                )
            ) from exc

    def get_pending(
        self,
        athlete_profile_id: UUID,
    ) -> tuple[
        PhysiologicalTestProposal,
        ...,
    ]:
        try:
            statement = (
                select(
                    PhysiologicalTestProposalModel
                )
                .where(
                    PhysiologicalTestProposalModel
                    .athlete_profile_id
                    == athlete_profile_id,
                    PhysiologicalTestProposalModel
                    .decision
                    == (
                        PhysiologicalTestDecision
                        .PENDING
                        .value
                    ),
                )
                .order_by(
                    PhysiologicalTestProposalModel
                    .proposed_date
                    .asc(),
                    PhysiologicalTestProposalModel
                    .created_at
                    .asc(),
                )
            )

            values = self.session.scalars(
                statement
            ).all()

            return tuple(
                self._to_domain(value)
                for value in values
            )

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise (
                PhysiologicalTestProposalRepositoryError(
                    "Impossible de charger "
                    "les propositions en attente."
                )
            ) from exc

    def list_since(
        self,
        athlete_profile_id: UUID,
        since: date,
    ) -> tuple[
        PhysiologicalTestProposal,
        ...,
    ]:
        try:
            statement = (
                select(
                    PhysiologicalTestProposalModel
                )
                .where(
                    PhysiologicalTestProposalModel
                    .athlete_profile_id
                    == athlete_profile_id,
                    PhysiologicalTestProposalModel
                    .proposed_date
                    >= since,
                )
                .order_by(
                    PhysiologicalTestProposalModel
                    .proposed_date
                    .desc(),
                    PhysiologicalTestProposalModel
                    .created_at
                    .desc(),
                )
            )

            values = self.session.scalars(
                statement
            ).all()

            return tuple(
                self._to_domain(value)
                for value in values
            )

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise (
                PhysiologicalTestProposalRepositoryError(
                    "Impossible de charger "
                    "l'historique des tests."
                )
            ) from exc

    @staticmethod
    def _to_domain(
        value: PhysiologicalTestProposalModel,
    ) -> PhysiologicalTestProposal:
        return PhysiologicalTestProposal(
            id=value.id,
            athlete_profile_id=(
                value.athlete_profile_id
            ),
            target_session_id=(
                value.target_session_id
            ),
            protocol=(
                PhysiologicalTestType(
                    value.protocol
                )
            ),
            target_metrics=tuple(
                PhysiologicalMetric(metric)
                for metric
                in value.target_metrics
            ),
            proposed_date=(
                value.proposed_date
            ),
            reason=value.reason,
            recommendation=(
                value.recommendation
            ),
            replacement_stimulus=(
                PhysiologicalTestReplacementStimulus(
                    value.replacement_stimulus
                )
            ),
            decision=(
                PhysiologicalTestDecision(
                    value.decision
                )
            ),
        )
