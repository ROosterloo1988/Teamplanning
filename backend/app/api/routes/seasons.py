from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_beheer
from app.db.session import get_db
from app.models.season import Season
from app.schemas.season import SeasonCreate, SeasonOut

router = APIRouter(prefix="/seasons", tags=["seasons"])


@router.get("", response_model=list[SeasonOut])
def list_seasons(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(Season).order_by(Season.startjaar.desc()).all()


@router.post("", response_model=SeasonOut, dependencies=[Depends(require_beheer)])
def create_season(payload: SeasonCreate, db: Session = Depends(get_db)):
    season = Season(naam=payload.naam, startjaar=payload.startjaar, eindjaar=payload.startjaar + 1)
    db.add(season)
    db.commit()
    db.refresh(season)
    return season


@router.post(
    "/{season_id}/activate", response_model=SeasonOut, dependencies=[Depends(require_beheer)]
)
def activate_season(season_id: int, db: Session = Depends(get_db)):
    """Maakt dit het actieve seizoen; nieuwe wedstrijden krijgen dit seizoen als default."""
    season = db.get(Season, season_id)
    if not season:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Seizoen niet gevonden")

    db.query(Season).filter(Season.id != season_id).update({Season.actief: False})
    season.actief = True
    db.commit()
    db.refresh(season)
    return season
