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
    session: Session = Depends(
        get_db
    ),
) -> dict[str, bool]:
    repository = (
        SqlPushSubscriptionRepository(
            session
        )
    )

    repository.delete_by_endpoint(
        payload.endpoint
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
