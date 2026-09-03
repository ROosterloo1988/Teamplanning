from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.player import Player


def notify_all_players(
    db: Session,
    *,
    type_: str,
    title: str,
    body: str | None = None,
    match_id: int | None = None,
) -> None:
    """Maakt een notificatie aan voor elke speler met een gekoppeld gebruikersaccount.

    Zie functioneel ontwerp v1 sectie 16 (fase 3, in-app notificaties).
    """
    user_ids = [
        row.user_id for row in db.query(Player.user_id).filter(Player.user_id.isnot(None)).all()
    ]
    for user_id in user_ids:
        db.add(
            Notification(
                user_id=user_id,
                type=type_,
                title=title,
                body=body,
                match_id=match_id,
            )
        )
