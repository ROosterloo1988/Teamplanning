import json
import logging

from pywebpush import WebPushException, webpush
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.push_subscription import PushSubscription

logger = logging.getLogger(__name__)


def send_push_to_user(db: Session, user_id: int, title: str, body: str | None = None, url: str = "/") -> None:
    """Stuurt een web push-melding naar alle geregistreerde toestellen van een gebruiker.

    Doet niets als er geen VAPID-sleutels zijn ingesteld (push staat dan uit).
    Verwijderde/ingetrokken abonnementen (404/410) worden meteen opgeruimd;
    de aanroeper is verantwoordelijk voor de uiteindelijke db.commit().
    """
    if not settings.VAPID_PRIVATE_KEY or not settings.VAPID_PUBLIC_KEY:
        return

    subscriptions = db.query(PushSubscription).filter(PushSubscription.user_id == user_id).all()
    if not subscriptions:
        return

    payload = json.dumps({"title": title, "body": body or "", "url": url})
    for sub in subscriptions:
        try:
            webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
                },
                data=payload,
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims={"sub": settings.VAPID_CLAIMS_EMAIL},
            )
        except WebPushException as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            if status_code in (404, 410):
                db.delete(sub)
            else:
                logger.warning("Push mislukt voor user %s: %s", user_id, exc)
    db.flush()
