"""Nachtelijke Teambeheer-synchronisatie, zie functioneel ontwerp v1 sectie 7.

Draait als achtergrondtaak binnen het backend-proces (APScheduler). Alleen
zinvol als de container daadwerkelijk internettoegang heeft tot
feeds.teambeheer.nl — een ontwikkelomgeving zonder die toegang faalt per
seizoen stil (gelogd + last_sync_status="error"), zonder de rest van de app
te breken.
"""

import logging
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.match import Match
from app.models.notification import Notification
from app.models.season import Season
from app.models.teambeheer import TeambeheerConfig
from app.services.notifications import send_response_reminders
from app.services.teambeheer import TeambeheerFetchError, sync_team_fixtures

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(timezone="UTC")

NOTIFICATION_READ_RETENTION_DAYS = 30


def run_nightly_sync() -> None:
    db = SessionLocal()
    try:
        configs = db.query(TeambeheerConfig).all()
        for config in configs:
            season = db.get(Season, config.season_id)
            if not season:
                continue
            try:
                sync_team_fixtures(db, config, season)
            except TeambeheerFetchError as exc:
                logger.warning("Teambeheer-sync mislukt voor seizoen %s: %s", season.naam, exc)
                db.rollback()
                config.last_sync_status = "error"
                config.last_sync_message = str(exc)
                db.commit()
            except Exception:
                logger.exception("Onverwachte fout bij Teambeheer-sync voor seizoen %s", season.naam)
                db.rollback()
    finally:
        db.close()


def run_notification_cleanup() -> None:
    """Ruimt de notifications-tabel op, die anders na een paar seizoenen
    ongelimiteerd blijft groeien: gelezen meldingen ouder dan
    NOTIFICATION_READ_RETENTION_DAYS (nog even terug te lezen op
    Meldingen, maar niet voor altijd), en meldingen die horen bij een
    wedstrijd uit een seizoen dat niet meer het actieve seizoen is."""
    db = SessionLocal()
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=NOTIFICATION_READ_RETENTION_DAYS)
        db.query(Notification).filter(
            Notification.read_at.isnot(None), Notification.read_at < cutoff
        ).delete(synchronize_session=False)

        active_season = db.query(Season).filter(Season.actief.is_(True)).first()
        if active_season:
            stale_ids = [
                row[0]
                for row in db.query(Notification.id)
                .join(Match, Notification.match_id == Match.id)
                .filter(Match.season_id.isnot(None), Match.season_id != active_season.id)
                .all()
            ]
            if stale_ids:
                db.query(Notification).filter(Notification.id.in_(stale_ids)).delete(
                    synchronize_session=False
                )

        db.commit()
    except Exception:
        logger.exception("Onverwachte fout bij opruimen van notificaties")
        db.rollback()
    finally:
        db.close()


def run_response_reminders() -> None:
    """Stuurt een herinnering (in-app + push) naar spelers die nog niet
    gereageerd hebben op een wedstrijd die nu op de REMINDER_DAYS_BEFORE-
    deadline zit."""
    db = SessionLocal()
    try:
        send_response_reminders(db, settings.REMINDER_DAYS_BEFORE)
        db.commit()
    except Exception:
        logger.exception("Onverwachte fout bij versturen van reactie-herinneringen")
        db.rollback()
    finally:
        db.close()


def start_scheduler() -> None:
    if settings.TEAMBEHEER_AUTO_SYNC:
        scheduler.add_job(
            run_nightly_sync,
            "cron",
            hour=settings.TEAMBEHEER_SYNC_HOUR,
            minute=settings.TEAMBEHEER_SYNC_MINUTE,
            id="teambeheer_nightly_sync",
            replace_existing=True,
        )
    scheduler.add_job(
        run_notification_cleanup,
        "cron",
        hour=settings.TEAMBEHEER_SYNC_HOUR,
        minute=(settings.TEAMBEHEER_SYNC_MINUTE + 15) % 60,
        id="notification_cleanup",
        replace_existing=True,
    )
    scheduler.add_job(
        run_response_reminders,
        "cron",
        hour=9,
        minute=0,
        id="response_reminders",
        replace_existing=True,
    )
    scheduler.start()


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
