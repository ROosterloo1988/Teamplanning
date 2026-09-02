from fastapi import APIRouter, Depends
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
    season = Season(**payload.model_dump())
    db.add(season)
    db.commit()
    db.refresh(season)
    return season
