from uuid import UUID
import os
from fastapi import (
    APIRouter,
    Depends,
    Request,
)
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)
from sqlalchemy.orm import Session

from opencoach.database.repositories.sql_push_subscription import (
    SqlPushSubscriptionRepository,
)
from opencoach.database.session import (
    get_db,
)

from opencoach.authentication import (
    get_current_user_id,
)


router = APIRouter(
    prefix="/api/push",
    tags=["push"],
)


class PushKeys(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid",
    )

    p256dh: str = Field(
        min_length=1,
    )

    auth: str = Field(
        min_length=1,
    )


class PushSubscriptionInput(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid",
    )

    endpoint: str = Field(
        min_length=1,
    )

    keys: PushKeys


class PushSubscriptionDelete(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid",
    )

    endpoint: str = Field(
        min_length=1,
    )


@router.post(
    "/subscriptions",
    status_code=201,
)
def subscribe(
    payload: PushSubscriptionInput,
    request: Request,
    user_id: UUID = Depends(
        get_current_user_id,
    ),
    session: Session = Depends(
        get_db
    ),
) -> dict[str, bool]:
    repository = (
        SqlPushSubscriptionRepository(
            session
        )
    )

    repository.save(
        user_id=user_id,
        endpoint=payload.endpoint,
        p256dh=payload.keys.p256dh,
        auth=payload.keys.auth,
        user_agent=request.headers.get(
            "user-agent"
        ),
    )

    return {
        "subscribed": True,
    }


@router.delete(
    "/subscriptions",
)
def unsubscribe(
    payload: PushSubscriptionDelete,
    user_id: UUID = Depends(
        get_current_user_id,
    ),
    session: Session = Depends(
        get_db
    ),
) -> dict[str, bool]:
    repository = (
        SqlPushSubscriptionRepository(
            session
        )
    )

    repository.delete_by_endpoint_for_user(
        payload.endpoint,
        user_id,
    )

    return {
        "subscribed": False,
    }


@router.get(
    "/public-key",
)
def get_public_key() -> dict[str, str]:
    public_key = os.getenv(
        "OPENCOACH_VAPID_PUBLIC_KEY",
        "",
    )

    if not public_key:
        return {
            "public_key": "",
        }

    return {
        "public_key": public_key,
    }


class PushBadgeReset(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid",
    )

    endpoint: str = Field(
        min_length=1,
    )


@router.post(
    "/badge/reset",
)
def reset_push_badge(
    payload: PushBadgeReset,
    user_id: UUID = Depends(
        get_current_user_id,
    ),
    session: Session = Depends(
        get_db
    ),
) -> dict[str, int]:
    repository = (
        SqlPushSubscriptionRepository(
            session
        )
    )

    repository.reset_badge_for_user(
        payload.endpoint,
        user_id,
    )

    return {
        "badge": 0,
    }


class PushEndpointInput(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    endpoint: str = Field(
        min_length=1,
    )


class PushPreferencesInput(
    PushEndpointInput
):
    system_enabled: bool
    sync_errors: bool
    backup_errors: bool
    training_reminder: bool


def _device_name(
    user_agent: str | None,
) -> str:
    value = (
        user_agent
        or ""
    ).lower()

    if "iphone" in value:
        return "iPhone"

    if "ipad" in value:
        return "iPad"

    if "android" in value:
        return "Android"

    if "windows" in value:
        return "PC Windows"

    if (
        "macintosh" in value
        or "mac os" in value
    ):
        return "Mac"

    return "Appareil"


def _browser_name(
    user_agent: str | None,
) -> str:
    value = (
        user_agent
        or ""
    ).lower()

    if "edg/" in value:
        return "Edge"

    if (
        "chrome/" in value
        and "edg/" not in value
    ):
        return "Chrome"

    if (
        "safari/" in value
        and "chrome/" not in value
    ):
        return "Safari"

    if "firefox/" in value:
        return "Firefox"

    return "Navigateur"


@router.post(
    "/devices",
)
def list_push_devices(
    payload: PushEndpointInput,
    user_id: UUID = Depends(
        get_current_user_id,
    ),
    session: Session = Depends(
        get_db
    ),
) -> dict[str, list[dict[str, object]]]:
    repository = (
        SqlPushSubscriptionRepository(
            session
        )
    )

    devices = []

    for subscription in repository.list_for_user(user_id):
        devices.append({
            "id": str(
                subscription.id
            ),
            "device_name": _device_name(
                subscription.user_agent
            ),
            "browser": _browser_name(
                subscription.user_agent
            ),
            "current": (
                subscription.endpoint
                == payload.endpoint
            ),
            "created_at": (
                subscription.created_at
                .isoformat()
            ),
            "updated_at": (
                subscription.updated_at
                .isoformat()
            ),
            "badge_count": (
                subscription.badge_count
            ),
        })

    return {
        "devices": devices,
    }


@router.post(
    "/preferences/read",
)
def get_push_preferences(
    payload: PushEndpointInput,
    user_id: UUID = Depends(
        get_current_user_id,
    ),
    session: Session = Depends(
        get_db
    ),
) -> dict[str, bool]:
    repository = (
        SqlPushSubscriptionRepository(
            session
        )
    )

    subscription = (
        repository.get_by_endpoint_for_user(
            payload.endpoint,
            user_id,
        )
    )

    if subscription is None:
        return {
            "system_enabled": True,
            "sync_errors": True,
            "backup_errors": True,
            "training_reminder": False,
        }

    return {
        "system_enabled": (
            subscription
            .system_notifications_enabled
        ),
        "sync_errors": (
            subscription
            .system_sync_errors_enabled
        ),
        "backup_errors": (
            subscription
            .system_backup_errors_enabled
        ),
        "training_reminder": (
            subscription
            .training_reminder_enabled
        ),
    }


@router.post(
    "/preferences",
)
def update_push_preferences(
    payload: PushPreferencesInput,
    user_id: UUID = Depends(
        get_current_user_id,
    ),
    session: Session = Depends(
        get_db
    ),
) -> dict[str, bool]:
    repository = (
        SqlPushSubscriptionRepository(
            session
        )
    )

    repository.update_preferences(
        user_id=user_id,
        endpoint=payload.endpoint,
        system_enabled=(
            payload.system_enabled
        ),
        sync_errors=(
            payload.sync_errors
        ),
        backup_errors=(
            payload.backup_errors
        ),
        training_reminder=(
            payload.training_reminder
        ),
    )

    return {
        "updated": True,
    }
