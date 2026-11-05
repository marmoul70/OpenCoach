from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from opencoach.database.models.notification import Notification


class NotificationRepositoryError(RuntimeError):
    """Erreur de persistance du centre de notifications."""


class SqlNotificationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    @staticmethod
    def _storage_datetime(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value
        return value.astimezone(timezone.utc).replace(tzinfo=None)

    def create(
        self,
        *,
        user_id: UUID,
        title: str,
        body: str,
        category: str,
        severity: str = "info",
        url: str | None = None,
    ) -> Notification:
        try:
            notification = Notification(
                user_id=user_id,
                title=title[:200],
                body=body,
                category=category,
                severity=severity,
                url=url,
            )
            self.session.add(notification)
            self.session.commit()
            self.session.refresh(notification)
            return notification
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise NotificationRepositoryError(
                "Impossible d'enregistrer la notification."
            ) from exc

    def list_for_user(
        self,
        user_id: UUID,
        *,
        unread_only: bool = False,
        limit: int = 30,
        offset: int = 0,
    ) -> tuple[list[Notification], int]:
        try:
            statement = select(Notification).where(
                Notification.user_id == user_id
            )
            count_statement = select(func.count()).select_from(
                Notification
            ).where(Notification.user_id == user_id)
            if unread_only:
                statement = statement.where(Notification.read_at.is_(None))
                count_statement = count_statement.where(
                    Notification.read_at.is_(None)
                )
            statement = (
                statement.order_by(
                    Notification.created_at.desc(),
                    Notification.id.desc(),
                )
                .limit(limit)
                .offset(offset)
            )
            items = list(self.session.scalars(statement))
            total = self.session.scalar(count_statement) or 0
            return items, total
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise NotificationRepositoryError(
                "Impossible de charger les notifications."
            ) from exc

    def unread_count(self, user_id: UUID) -> int:
        try:
            statement = select(func.count()).select_from(
                Notification
            ).where(
                Notification.user_id == user_id,
                Notification.read_at.is_(None),
            )
            return int(self.session.scalar(statement) or 0)
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise NotificationRepositoryError(
                "Impossible de compter les notifications non lues."
            ) from exc

    def mark_read(self, notification_id: UUID, user_id: UUID) -> bool:
        try:
            notification = self.session.scalar(
                select(Notification).where(
                    Notification.id == notification_id,
                    Notification.user_id == user_id,
                )
            )
            if notification is None:
                return False
            if notification.read_at is None:
                notification.read_at = self._storage_datetime(
                    datetime.now(timezone.utc)
                )
                self.session.commit()
            return True
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise NotificationRepositoryError(
                "Impossible de marquer la notification comme lue."
            ) from exc

    def mark_all_read(self, user_id: UUID) -> int:
        try:
            result = self.session.execute(
                update(Notification)
                .where(
                    Notification.user_id == user_id,
                    Notification.read_at.is_(None),
                )
                .values(read_at=self._storage_datetime(datetime.now(timezone.utc)))
            )
            self.session.commit()
            return int(result.rowcount or 0)
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise NotificationRepositoryError(
                "Impossible de marquer les notifications comme lues."
            ) from exc

    def delete_one(self, notification_id: UUID, user_id: UUID) -> bool:
        try:
            result = self.session.execute(
                delete(Notification).where(
                    Notification.id == notification_id,
                    Notification.user_id == user_id,
                )
            )
            self.session.commit()
            return bool(result.rowcount)
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise NotificationRepositoryError(
                "Impossible de supprimer la notification."
            ) from exc

    def delete_all(self, user_id: UUID) -> int:
        try:
            result = self.session.execute(
                delete(Notification).where(
                    Notification.user_id == user_id
                )
            )
            self.session.commit()
            return int(result.rowcount or 0)
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise NotificationRepositoryError(
                "Impossible de supprimer les notifications."
            ) from exc
