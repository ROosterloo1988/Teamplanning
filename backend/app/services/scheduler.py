"""Nachtelijke Teambeheer-synchronisatie, zie functioneel ontwerp v1 sectie 7.

Draait als achtergrondtaak binnen het backend-proces (APScheduler). Alleen
zinvol als de container daadwerkelijk internettoegang heeft tot
feeds.teambeheer.nl — een ontwikkelomgeving zonder die toegang faalt per
seizoen stil (gelogd + last_sync_status="error"), zonder de rest van de app
te breken.
"""

import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.season import Season
from app.models.teambeheer import TeambeheerConfig
from app.services.teambeheer import TeambeheerFetchError, sync_team_fixtures

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(timezone="UTC")


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


def start_scheduler() -> None:
    if not settings.TEAMBEHEER_AUTO_SYNC:
        return
    scheduler.add_job(
        run_nightly_sync,
        "cron",
        hour=settings.TEAMBEHEER_SYNC_HOUR,
        minute=settings.TEAMBEHEER_SYNC_MINUTE,
        id="teambeheer_nightly_sync",
        replace_existing=True,
    )
    scheduler.start()


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
