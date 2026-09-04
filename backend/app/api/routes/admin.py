from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_beheer
from app.db.session import get_db
from app.models.availability import Availability
from app.models.enums import AvailabilityStatus
from app.models.match import Match
from app.models.player import Player

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_beheer)])


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    total_players = db.query(Player).count()
    total_matches = db.query(Match).count()

    complete_matches = 0
    missing_matches = 0
    for match in db.query(Match).all():
        statuses = [a.status for a in match.availabilities]
        if statuses and all(s != AvailabilityStatus.NO_RESPONSE for s in statuses):
            complete_matches += 1
        elif any(s == AvailabilityStatus.NO_RESPONSE for s in statuses):
            missing_matches += 1

    return {
        "spelers": total_players,
        "wedstrijden": total_matches,
        "wedstrijden_compleet": complete_matches,
        "wedstrijden_missen_antwoorden": missing_matches,
    }
