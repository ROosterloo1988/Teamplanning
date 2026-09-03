from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_beheer, require_captain
from app.core.config import settings
from app.db.session import get_db
from app.models.availability import Availability
from app.models.match import Match
from app.models.player import Player
from app.models.enums import AvailabilityStatus
from app.schemas.match import MatchCreate, MatchOut
from app.schemas.reminder import MatchReminderOut

router = APIRouter(prefix="/matches", tags=["matches"])


@router.get(
    "/reminders", response_model=list[MatchReminderOut], dependencies=[Depends(require_captain)]
)
def match_reminders(days: int | None = None, db: Session = Depends(get_db)):
    """Wedstrijden binnen N dagen met spelers die nog niet gereageerd hebben (ontwerp sectie 11)."""
    window = days if days is not None else settings.REMINDER_DAYS_BEFORE
    today = date.today()
    matches = (
        db.query(Match)
        .filter(Match.datum >= today, Match.datum <= today + timedelta(days=window))
        .order_by(Match.datum)
        .all()
    )

    reminders: list[MatchReminderOut] = []
    for match in matches:
        counts = (
            db.query(Availability.status, func.count())
            .filter(Availability.match_id == match.id)
            .group_by(Availability.status)
            .all()
        )
        total = sum(count for _, count in counts)
        missing = next((count for s, count in counts if s == AvailabilityStatus.NO_RESPONSE), 0)
        if missing > 0:
            reminders.append(MatchReminderOut(match=match, total=total, missing=missing))
    return reminders


@router.get("", response_model=list[MatchOut])
def list_matches(
    upcoming_only: bool = False,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    query = db.query(Match)
    if upcoming_only:
        query = query.filter(Match.datum >= date.today())
    return query.order_by(Match.datum).all()


@router.get("/{match_id}", response_model=MatchOut)
def get_match(match_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    match = db.get(Match, match_id)
    if not match:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wedstrijd niet gevonden")
    return match


@router.post("", response_model=MatchOut, dependencies=[Depends(require_beheer)])
def create_match(payload: MatchCreate, db: Session = Depends(get_db)):
    match = Match(**payload.model_dump())
    db.add(match)
    db.flush()

    # Maak meteen "geen antwoord"-beschikbaarheid aan voor alle actieve spelers.
    for player in db.query(Player).all():
        db.add(
            Availability(
                match_id=match.id,
                player_id=player.id,
                status=AvailabilityStatus.NO_RESPONSE,
            )
        )

    db.commit()
    db.refresh(match)
    return match
