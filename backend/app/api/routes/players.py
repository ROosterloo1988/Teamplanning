import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_beheer
from app.core.security import hash_password
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.player import Player
from app.models.user import User
from app.schemas.player import PlayerCreate, PlayerOut
from app.schemas.user import UserCreate, UserOut

router = APIRouter(prefix="/players", tags=["players"])


@router.get("", response_model=list[PlayerOut])
def list_players(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(Player).order_by(Player.naam).all()


@router.post("", response_model=PlayerOut, dependencies=[Depends(require_beheer)])
def create_player(payload: PlayerCreate, db: Session = Depends(get_db)):
    player = Player(**payload.model_dump())
    db.add(player)
    db.commit()
    db.refresh(player)
    return player


@router.post("/with-account", response_model=UserOut, dependencies=[Depends(require_beheer)])
def create_player_with_account(payload: UserCreate, db: Session = Depends(get_db)):
    """Maak in één stap een gebruiker + bijbehorende speler aan (Beheer > Spelers)."""
    if payload.email and db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="E-mailadres al in gebruik")

    if payload.rol in (UserRole.CAPTAIN, UserRole.BEHEER):
        if not payload.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ontgrendelwachtwoord is verplicht voor captain/beheer",
            )
        password = payload.password
    else:
        # Speler logt in door op zijn naam te klikken; dit wachtwoord wordt
        # nooit gebruikt, maar de kolom staat niet leeg toe.
        password = payload.password or secrets.token_urlsafe(24)

    user = User(
        naam=payload.naam,
        email=payload.email,
        hashed_password=hash_password(password),
        rol=payload.rol,
        actief=payload.actief,
    )
    db.add(user)
    db.flush()

    player = Player(user_id=user.id, naam=payload.naam, team_id=payload.team_id)
    db.add(player)
    db.commit()
    db.refresh(user)

    return UserOut(
        id=user.id,
        naam=user.naam,
        email=user.email,
        rol=user.rol,
        actief=user.actief,
        player_id=player.id,
    )
