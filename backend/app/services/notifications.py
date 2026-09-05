from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models.availability import Availability
from app.models.enums import AvailabilityStatus, MatchStatus
from app.models.match import Match
from app.models.notification import Notification
from app.models.player import Player
from app.services.push import send_push_to_user


def notify_all_players(
    db: Session,
    *,
    type_: str,
    title: str,
    body: str | None = None,
    match_id: int | None = None,
) -> None:
    """Maakt een notificatie aan voor elke speler met een gekoppeld gebruikersaccount.

    Zie functioneel ontwerp v1 sectie 16 (fase 3, in-app notificaties). Stuurt
    daarnaast, indien geabonneerd, een web push-melding naar het toestel.
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
    for user_id in user_ids:
        send_push_to_user(db, user_id, title, body, url="/meldingen")


def send_response_reminders(db: Session, days_before: int) -> None:
    """Herinnert spelers die nog niet gereageerd hebben aan een wedstrijd die
    precies `days_before` dagen wegligt (de REMINDER_DAYS_BEFORE-deadline uit
    functioneel ontwerp v1 sectie 11). Bedoeld om één keer per dag te draaien
    vanuit de scheduler; is idempotent (skipt spelers die al een herinnering
    voor deze wedstrijd hebben gehad)."""
    target_date = date.today() + timedelta(days=days_before)
    matches = (
        db.query(Match)
        .filter(Match.datum == target_date, Match.status == MatchStatus.GEPLAND)
        .all()
    )
    for match in matches:
        missing = (
            db.query(Availability, Player)
            .join(Player, Availability.player_id == Player.id)
            .filter(
                Availability.match_id == match.id,
                Availability.status == AvailabilityStatus.NO_RESPONSE,
                Player.user_id.isnot(None),
            )
            .all()
        )
        for _availability, player in missing:
            already_sent = (
                db.query(Notification.id)
                .filter(
                    Notification.user_id == player.user_id,
                    Notification.match_id == match.id,
                    Notification.type == "response_reminder",
                )
                .first()
            )
            if already_sent:
                continue
            title = "⏰ Nog niet gereageerd"
            body = (
                f"{match.thuisteam} - {match.uitteam} op {match.datum.strftime('%d-%m-%Y')} — "
                "geef je beschikbaarheid nog even door."
            )
            db.add(
                Notification(
                    user_id=player.user_id,
                    type="response_reminder",
                    title=title,
                    body=body,
                    match_id=match.id,
                )
            )
            send_push_to_user(db, player.user_id, title, body, url="/speler")
