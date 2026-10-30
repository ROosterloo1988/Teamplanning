from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_beheer
from app.db.session import get_db
from app.models.season import Season
from app.models.teambeheer import TeambeheerConfig
from app.schemas.teambeheer import (
    TeambeheerConfigOut,
    TeambeheerConfigUpdate,
    TeambeheerFixturePreview,
    TeambeheerSyncResult,
)
from app.services.teambeheer import TeambeheerFetchError, preview_team_fixtures, sync_team_fixtures

router = APIRouter(prefix="/teambeheer", tags=["teambeheer"], dependencies=[Depends(require_beheer)])


def _get_season(db: Session, season_id: int) -> Season:
    season = db.get(Season, season_id)
    if not season:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Seizoen niet gevonden")
    return season


def _get_config(db: Session, season_id: int) -> TeambeheerConfig:
    config = db.query(TeambeheerConfig).filter(TeambeheerConfig.season_id == season_id).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nog geen Teambeheer-koppeling ingesteld voor dit seizoen",
        )
    return config


@router.get("/config/{season_id}", response_model=TeambeheerConfigOut)
def get_config(season_id: int, db: Session = Depends(get_db)):
    return _get_config(db, season_id)


@router.put("/config/{season_id}", response_model=TeambeheerConfigOut)
def upsert_config(season_id: int, payload: TeambeheerConfigUpdate, db: Session = Depends(get_db)):
    _get_season(db, season_id)
    config = db.query(TeambeheerConfig).filter(TeambeheerConfig.season_id == season_id).first()
    if not config:
        config = TeambeheerConfig(season_id=season_id)
        db.add(config)

    config.bond_id = payload.bond_id
    config.poule = payload.poule
    config.team_id = payload.team_id
    db.commit()
    db.refresh(config)
    return config


@router.get("/preview/{season_id}", response_model=list[TeambeheerFixturePreview])
def preview(season_id: int, db: Session = Depends(get_db)):
    season = _get_season(db, season_id)
    config = _get_config(db, season_id)
    try:
        return preview_team_fixtures(db, config, season)
    except TeambeheerFetchError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


@router.post("/sync/{season_id}", response_model=TeambeheerSyncResult)
def sync_now(season_id: int, db: Session = Depends(get_db)):
    season = _get_season(db, season_id)
    config = _get_config(db, season_id)
    try:
        return sync_team_fixtures(db, config, season)
    except TeambeheerFetchError as exc:
        config.last_sync_status = "error"
        config.last_sync_message = str(exc)
        db.commit()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
