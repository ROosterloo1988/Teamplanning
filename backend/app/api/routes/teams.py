from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_beheer
from app.db.session import get_db
from app.models.team import Team
from app.schemas.team import TeamCreate, TeamOut

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("", response_model=list[TeamOut])
def list_teams(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(Team).order_by(Team.naam).all()


@router.post("", response_model=TeamOut, dependencies=[Depends(require_beheer)])
def create_team(payload: TeamCreate, db: Session = Depends(get_db)):
    team = Team(**payload.model_dump())
    db.add(team)
    db.commit()
    db.refresh(team)
    return team
