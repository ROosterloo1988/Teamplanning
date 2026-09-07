from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_beheer
from app.core.config import settings
from app.db.session import get_db
from app.models.season import Season
from app.models.teambeheer import TeambeheerConfig
from app.schemas.season import SeasonCreate, SeasonOut
from app.services.teambeheer import season_code

router = APIRouter(prefix="/seasons", tags=["seasons"])


def _stand_url(config: TeambeheerConfig, startjaar: int) -> str:
    return (
        f"{settings.TEAMBEHEER_BASE_URL}/web/stand/"
        f"?d={config.bond_id}&div={config.poule}&s={season_code(startjaar)}"
    )


@router.get("", response_model=list[SeasonOut])
def list_seasons(db: Session = Depends(get_db), _=Depends(get_current_user)):
    seasons = db.query(Season).order_by(Season.startjaar.desc()).all()
    configs = {
        c.season_id: c
        for c in db.query(TeambeheerConfig)
        .filter(TeambeheerConfig.season_id.in_([s.id for s in seasons]))
        .all()
    }
    return [
        SeasonOut.model_validate(season).model_copy(
            update={
                "stand_url": _stand_url(configs[season.id], season.startjaar)
                if season.id in configs
                else None
            }
        )
        for season in seasons
    ]


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
