from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_captain
from app.db.session import get_db
from app.models.lineup import Lineup, LineupPlayer
from app.models.player import Player
from app.models.user import User
from app.schemas.lineup import LineupOut, LineupUpdate
from app.services.audit import log_change

router = APIRouter(prefix="/lineups", tags=["lineups"])


def _to_out(lineup: Lineup) -> LineupOut:
    return LineupOut(
        id=lineup.id,
        match_id=lineup.match_id,
        published=lineup.published,
        published_at=lineup.published_at,
        player_ids=[lp.player_id for lp in lineup.players],
    )


def _get_or_create(db: Session, match_id: int) -> Lineup:
    lineup = db.query(Lineup).filter(Lineup.match_id == match_id).first()
    if not lineup:
        lineup = Lineup(match_id=match_id, published=False)
        db.add(lineup)
        db.flush()
    return lineup


def _player_names(db: Session, player_ids: list[int]) -> str:
    if not player_ids:
        return ""
    names = db.query(Player.naam).filter(Player.id.in_(player_ids)).all()
    return ", ".join(sorted(n for (n,) in names))


@router.get("/match/{match_id}", response_model=LineupOut)
def get_lineup(match_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    lineup = db.query(Lineup).filter(Lineup.match_id == match_id).first()
    if not lineup:
        return LineupOut(id=0, match_id=match_id, published=False, published_at=None, player_ids=[])
    return _to_out(lineup)


@router.put("/match/{match_id}", response_model=LineupOut, dependencies=[Depends(require_captain)])
def set_lineup(
    match_id: int,
    payload: LineupUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lineup = _get_or_create(db, match_id)

    old_names = _player_names(db, [lp.player_id for lp in lineup.players])

    lineup.players.clear()
    db.flush()
    for player_id in payload.player_ids:
        lineup.players.append(LineupPlayer(lineup_id=lineup.id, player_id=player_id))
    db.flush()

    new_names = _player_names(db, payload.player_ids)
    if old_names != new_names:
        log_change(
            db,
            user_id=current_user.id,
            entity_type="lineup",
            entity_id=lineup.id,
            action="update",
            old_value=old_names or None,
            new_value=new_names or None,
        )

    db.commit()
    db.refresh(lineup)
    return _to_out(lineup)


@router.post(
    "/match/{match_id}/publish", response_model=LineupOut, dependencies=[Depends(require_captain)]
)
def publish_lineup(
    match_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    lineup = db.query(Lineup).filter(Lineup.match_id == match_id).first()
    if not lineup:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Geen opstelling om te publiceren")

    lineup.published = True
    lineup.published_at = datetime.now(timezone.utc)
    log_change(
        db,
        user_id=current_user.id,
        entity_type="lineup",
        entity_id=lineup.id,
        action="publish",
        old_value=None,
        new_value=_player_names(db, [lp.player_id for lp in lineup.players]) or None,
    )
    db.commit()
    db.refresh(lineup)
    return _to_out(lineup)
