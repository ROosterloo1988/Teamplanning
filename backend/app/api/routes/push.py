from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.push_subscription import PushSubscription
from app.models.user import User
from app.schemas.push import PushSubscriptionIn, PushUnsubscribeIn

router = APIRouter(prefix="/push", tags=["push"])


@router.get("/vapid-public-key")
def vapid_public_key(current_user: User = Depends(get_current_user)):
    return {"public_key": settings.VAPID_PUBLIC_KEY}


@router.post("/subscribe", status_code=status.HTTP_204_NO_CONTENT)
def subscribe(
    payload: PushSubscriptionIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = db.query(PushSubscription).filter(PushSubscription.endpoint == payload.endpoint).first()
    if existing:
        existing.user_id = current_user.id
        existing.p256dh = payload.keys.p256dh
        existing.auth = payload.keys.auth
    else:
        db.add(
            PushSubscription(
                user_id=current_user.id,
                endpoint=payload.endpoint,
                p256dh=payload.keys.p256dh,
                auth=payload.keys.auth,
            )
        )
    db.commit()


@router.post("/unsubscribe", status_code=status.HTTP_204_NO_CONTENT)
def unsubscribe(
    payload: PushUnsubscribeIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db.query(PushSubscription).filter(
        PushSubscription.endpoint == payload.endpoint, PushSubscription.user_id == current_user.id
    ).delete()
    db.commit()
