from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, require_captain
from app.db.session import get_db
from app.models.availability import Availability
from app.models.match import Match
from app.models.user import User
from app.schemas.availability import AvailabilityOut, AvailabilityUpdate, AvailabilityWithPlayer
from app.services.audit import log_change

router = APIRouter(prefix="/availability", tags=["availability"])


@router.get("/me", response_model=list[AvailabilityOut])
def my_availability(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user.player:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Geen spelerprofiel gekoppeld")
    return (
        db.query(Availability)
        .join(Match)
        .filter(Availability.player_id == current_user.player.id)
        .order_by(Match.datum)
        .all()
    )


@router.put("/{match_id}", response_model=AvailabilityOut)
def set_my_availability(
    match_id: int,
    payload: AvailabilityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.player:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Geen spelerprofiel gekoppeld")

    availability = (
        db.query(Availability)
        .filter(Availability.match_id == match_id, Availability.player_id == current_user.player.id)
        .first()
    )
    if not availability:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wedstrijd niet gevonden")

    old_status = availability.status
    availability.status = payload.status
    log_change(
        db,
        user_id=current_user.id,
        entity_type="availability",
        entity_id=availability.id,
        action="update",
        old_value=old_status.value,
        new_value=payload.status.value,
    )
    db.commit()
    db.refresh(availability)
    return availability


@router.get(
    "/match/{match_id}",
    response_model=list[AvailabilityWithPlayer],
    dependencies=[Depends(require_captain)],
)
def match_availability(match_id: int, db: Session = Depends(get_db)):
    rows = (
        db.query(Availability)
        .options(joinedload(Availability.player))
        .filter(Availability.match_id == match_id)
        .all()
    )
    return [
        AvailabilityWithPlayer(
            id=row.id,
            match_id=row.match_id,
            player_id=row.player_id,
            status=row.status,
            updated_at=row.updated_at,
            player_naam=row.player.naam,
        )
        for row in rows
    ]
