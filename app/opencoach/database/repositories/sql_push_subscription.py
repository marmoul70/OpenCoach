from sqlalchemy import (
    delete,
    select,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from opencoach.database.models import (
    PushSubscription,
)


class PushSubscriptionRepositoryError(
    RuntimeError
):
    pass


class SqlPushSubscriptionRepository:
    def __init__(
        self,
        session: Session,
    ) -> None:
        self.session = session

    def list_all(
        self,
    ) -> list[PushSubscription]:
        try:
            statement = (
                select(
                    PushSubscription
                )
                .order_by(
                    PushSubscription.created_at
                )
            )

            return list(
                self.session.scalars(
                    statement
                )
            )

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise PushSubscriptionRepositoryError(
                "Impossible de charger "
                "les abonnements push."
            ) from exc

    def save(
        self,
        *,
        endpoint: str,
        p256dh: str,
        auth: str,
        user_agent: str | None,
    ) -> PushSubscription:
        try:
            subscription = (
                self.session.scalar(
                    select(
                        PushSubscription
                    ).where(
                        PushSubscription.endpoint
                        == endpoint
                    )
                )
            )

            if subscription is None:
                subscription = (
                    PushSubscription(
                        endpoint=endpoint,
                        p256dh=p256dh,
                        auth=auth,
                        user_agent=user_agent,
                    )
                )

                self.session.add(
                    subscription
                )
            else:
                subscription.p256dh = (
                    p256dh
                )
                subscription.auth = auth
                subscription.user_agent = (
                    user_agent
                )

            self.session.commit()
            self.session.refresh(
                subscription
            )

            return subscription

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise PushSubscriptionRepositoryError(
                "Impossible d'enregistrer "
                "l'abonnement push."
            ) from exc

    def delete_by_endpoint(
        self,
        endpoint: str,
    ) -> None:
        try:
            self.session.execute(
                delete(
                    PushSubscription
                ).where(
                    PushSubscription.endpoint
                    == endpoint
                )
            )

            self.session.commit()

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise PushSubscriptionRepositoryError(
                "Impossible de supprimer "
                "l'abonnement push."
            ) from exc

    def increment_badge(
        self,
        endpoint: str,
    ) -> int:
        try:
            subscription = self.session.scalar(
                select(
                    PushSubscription
                ).where(
                    PushSubscription.endpoint
                    == endpoint
                )
            )

            if subscription is None:
                raise PushSubscriptionRepositoryError(
                    "Abonnement Push introuvable."
                )

            subscription.badge_count += 1

            self.session.commit()
            self.session.refresh(
                subscription
            )

            return subscription.badge_count

        except PushSubscriptionRepositoryError:
            self.session.rollback()
            raise

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise PushSubscriptionRepositoryError(
                "Impossible d'incrémenter "
                "le badge Push."
            ) from exc

    def reset_badge(
        self,
        endpoint: str,
    ) -> None:
        try:
            subscription = self.session.scalar(
                select(
                    PushSubscription
                ).where(
                    PushSubscription.endpoint
                    == endpoint
                )
            )

            if subscription is None:
                return

            subscription.badge_count = 0

            self.session.commit()
            self.session.refresh(
                subscription
            )

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise PushSubscriptionRepositoryError(
                "Impossible de remettre "
                "le badge Push à zéro."
            ) from exc
