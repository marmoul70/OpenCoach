from datetime import timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from opencoach.authentication import get_current_user_id
from opencoach.database.repositories.sql_notification import (
    SqlNotificationRepository,
)
from opencoach.database.session import get_db


router = APIRouter(
    prefix="/api/notifications",
    tags=["notifications"],
)


class NotificationItem(BaseModel):
    id: UUID
    title: str
    body: str
    category: str
    severity: str
    url: str | None
    created_at: str
    read_at: str | None

    @classmethod
    def from_model(cls, notification) -> "NotificationItem":
        created_at = notification.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        read_at = notification.read_at
        if read_at is not None and read_at.tzinfo is None:
            read_at = read_at.replace(tzinfo=timezone.utc)
        return cls(
            id=notification.id,
            title=notification.title,
            body=notification.body,
            category=notification.category,
            severity=notification.severity,
            url=notification.url,
            created_at=created_at.isoformat(),
            read_at=read_at.isoformat() if read_at else None,
        )


class NotificationListResponse(BaseModel):
    items: list[NotificationItem]
    total: int
    unread_count: int
    limit: int
    offset: int


@router.get("", response_model=NotificationListResponse)
def list_notifications(
    unread_only: bool = False,
    limit: int = Query(default=30, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user_id: UUID = Depends(get_current_user_id),
    session: Session = Depends(get_db),
) -> NotificationListResponse:
    repository = SqlNotificationRepository(session)
    items, total = repository.list_for_user(
        user_id,
        unread_only=unread_only,
        limit=limit,
        offset=offset,
    )
    return NotificationListResponse(
        items=[NotificationItem.from_model(item) for item in items],
        total=total,
        unread_count=repository.unread_count(user_id),
        limit=limit,
        offset=offset,
    )


@router.get("/unread-count")
def unread_count(
    user_id: UUID = Depends(get_current_user_id),
    session: Session = Depends(get_db),
) -> dict[str, int]:
    return {
        "unread_count": SqlNotificationRepository(session).unread_count(user_id)
    }


@router.post("/read-all")
def mark_all_read(
    user_id: UUID = Depends(get_current_user_id),
    session: Session = Depends(get_db),
) -> dict[str, int]:
    updated = SqlNotificationRepository(session).mark_all_read(user_id)
    return {"updated": updated}


@router.delete("/all")
def delete_all_notifications(
    user_id: UUID = Depends(get_current_user_id),
    session: Session = Depends(get_db),
) -> dict[str, int]:
    deleted = SqlNotificationRepository(session).delete_all(user_id)
    return {"deleted": deleted}


@router.post("/{notification_id}/read")
def mark_notification_read(
    notification_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    session: Session = Depends(get_db),
) -> Response:
    updated = SqlNotificationRepository(session).mark_read(
        notification_id,
        user_id,
    )
    return Response(
        status_code=status.HTTP_204_NO_CONTENT if updated else status.HTTP_404_NOT_FOUND
    )


@router.delete("/{notification_id}")
def delete_notification(
    notification_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    session: Session = Depends(get_db),
) -> Response:
    deleted = SqlNotificationRepository(session).delete_one(
        notification_id,
        user_id,
    )
    return Response(
        status_code=status.HTTP_204_NO_CONTENT if deleted else status.HTTP_404_NOT_FOUND
    )
