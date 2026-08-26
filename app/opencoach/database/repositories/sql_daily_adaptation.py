"""Repository SQLAlchemy des propositions quotidiennes."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from opencoach.coaching.daily_adaptation import (
    AdaptationDecision,
    CoachAdaptationProposal,
)
from opencoach.database.models.daily_adaptation import (
    DailyAdaptationProposal as DailyAdaptationProposalModel,
)
from opencoach.database.repositories.daily_adaptation import (
    DailyAdaptationRepository,
    DailyAdaptationRepositoryError,
)


class SqlDailyAdaptationRepository(
    DailyAdaptationRepository
):
    """Implémentation SQLAlchemy des propositions."""

    def __init__(
        self,
        session: Session,
    ) -> None:
        self.session = session

    def save(
        self,
        athlete_profile_id: UUID,
        proposal: CoachAdaptationProposal,
    ) -> CoachAdaptationProposal:
        try:
            database_proposal = None

            if proposal.id is not None:
                database_proposal = self.session.scalar(
                    select(
                        DailyAdaptationProposalModel
                    ).where(
                        DailyAdaptationProposalModel.id
                        == proposal.id,
                        DailyAdaptationProposalModel
                        .athlete_profile_id
                        == athlete_profile_id,
                    )
                )

            if database_proposal is None:
                database_proposal = self.session.scalar(
                    select(
                        DailyAdaptationProposalModel
                    ).where(
                        DailyAdaptationProposalModel
                        .athlete_profile_id
                        == athlete_profile_id,
                        DailyAdaptationProposalModel
                        .checkin_id
                        == proposal.checkin_id,
                    )
                )

            if database_proposal is None:
                database_proposal = (
                    DailyAdaptationProposalModel(
                        athlete_profile_id=(
                            athlete_profile_id
                        ),
                        checkin_id=proposal.checkin_id,
                        reason=proposal.reason,
                        recommendation=(
                            proposal.recommendation
                        ),
                        decision=proposal.decision.value,
                    )
                )

                self.session.add(
                    database_proposal
                )

            else:
                database_proposal.reason = (
                    proposal.reason
                )
                database_proposal.recommendation = (
                    proposal.recommendation
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

            raise DailyAdaptationRepositoryError(
                "Impossible d'enregistrer "
                "la proposition d'adaptation."
            ) from exc

    def delete_for_checkin(
        self,
        athlete_profile_id: UUID,
        checkin_id: UUID,
    ) -> None:
        try:
            database_proposal = self.session.scalar(
                select(
                    DailyAdaptationProposalModel
                ).where(
                    DailyAdaptationProposalModel
                    .athlete_profile_id
                    == athlete_profile_id,
                    DailyAdaptationProposalModel
                    .checkin_id
                    == checkin_id,
                )
            )

            if database_proposal is None:
                return

            self.session.delete(
                database_proposal
            )

            self.session.commit()

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise DailyAdaptationRepositoryError(
                "Impossible de supprimer "
                "la proposition d'adaptation."
            ) from exc

    def get_for_checkin(
        self,
        athlete_profile_id: UUID,
        checkin_id: UUID,
    ) -> CoachAdaptationProposal | None:
        try:
            database_proposal = self.session.scalar(
                select(
                    DailyAdaptationProposalModel
                ).where(
                    DailyAdaptationProposalModel
                    .athlete_profile_id
                    == athlete_profile_id,
                    DailyAdaptationProposalModel
                    .checkin_id
                    == checkin_id,
                )
            )

            if database_proposal is None:
                return None

            return self._to_domain(
                database_proposal
            )

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise DailyAdaptationRepositoryError(
                "Impossible de charger "
                "la proposition d'adaptation."
            ) from exc

    @staticmethod
    def _to_domain(
        database_proposal: (
            DailyAdaptationProposalModel
        ),
    ) -> CoachAdaptationProposal:
        return CoachAdaptationProposal(
            id=database_proposal.id,
            checkin_id=database_proposal.checkin_id,
            reason=database_proposal.reason,
            recommendation=(
                database_proposal.recommendation
            ),
            decision=AdaptationDecision(
                database_proposal.decision
            ),
        )
