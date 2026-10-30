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
    TeamFeedDiagnosticsOut,
)
from app.services.teambeheer import (
    TeambeheerFetchError,
    preview_team_fixtures,
    season_code,
    sync_team_fixtures,
)
from app.services.teambeheer_team_feed import diagnose_team_feed, resolve_team_date

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


@router.get("/team-feed-test/{season_id}", response_model=TeamFeedDiagnosticsOut)
def team_feed_test(season_id: int, db: Session = Depends(get_db)):
    """Beta, read-only: haalt de nieuwe /web/team-feed op (die ook
    bekerwedstrijden toont) en toont precies wat er geparst wordt, zonder
    iets op te slaan. Los van de echte sync — bedoeld om op de live server
    uit te proberen voordat we 'm eventueel samenvoegen."""
    season = _get_season(db, season_id)
    config = _get_config(db, season_id)
    s_code = season_code(season.startjaar)
    diag = diagnose_team_feed(config.bond_id, config.team_id, s_code)

    fixtures_out = [
        {
            "official_id": f.official_id,
            "ronde": f.ronde,
            "is_beker": f.is_beker,
            "datum": resolve_team_date(f.datum_raw),
            "datum_raw": f.datum_raw,
            "thuisteam": f.thuis_naam.strip(),
            "uitteam": f.uit_naam.strip(),
            "uitslag": f.score.strip() or None,
            "uitslag_url": f.score_url,
        }
        for f in diag.fixtures
    ]
    return {
        "url": diag.url,
        "html_length": diag.html_length,
        "computer_section_found": diag.computer_section_found,
        "wedstrijden_header_found": diag.wedstrijden_header_found,
        "table_found": diag.table_found,
        "tbody_found": diag.tbody_found,
        "raw_row_count": diag.raw_row_count,
        "skipped_no_title": diag.skipped_no_title,
        "skipped_vrije_week": diag.skipped_vrije_week,
        "parsed_count": diag.parsed_count,
        "error": diag.error,
        "fixtures": fixtures_out,
    }
