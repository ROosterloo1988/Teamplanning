import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_beheer
from app.core.security import hash_password
from app.db.session import get_db
from app.models.availability import Availability
from app.models.enums import AvailabilityStatus, UserRole
from app.models.match import Match
from app.models.player import Player
from app.models.user import User
from app.schemas.player import PlayerCreate, PlayerOut
from app.schemas.user import UserCreate, UserOut, UserUpdate

router = APIRouter(prefix="/players", tags=["players"])


@router.get("", response_model=list[PlayerOut])
def list_players(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(Player).order_by(Player.naam).all()


@router.get("/with-accounts", response_model=list[UserOut], dependencies=[Depends(require_beheer)])
def list_players_with_accounts(db: Session = Depends(get_db)):
    """Speler+account overzicht voor Beheer > Spelers (naam, rol, actief, e-mail)."""
    players = db.query(Player).join(User, Player.user_id == User.id).order_by(Player.naam).all()
    return [
        UserOut(
            id=player.user.id,
            naam=player.user.naam,
            email=player.user.email,
            rol=player.user.rol,
            actief=player.user.actief,
            player_id=player.id,
        )
        for player in players
    ]


def _backfill_availability(db: Session, player_id: int) -> None:
    """Nieuwe spelers krijgen anders alleen beschikbaarheid voor wedstrijden
    die na hun aanmaken worden aangemaakt (via sync of handmatig) — zonder
    dit kunnen ze bestaande wedstrijden niet invullen."""
    for (match_id,) in db.query(Match.id).all():
        db.add(Availability(match_id=match_id, player_id=player_id, status=AvailabilityStatus.NO_RESPONSE))


@router.post("", response_model=PlayerOut, dependencies=[Depends(require_beheer)])
def create_player(payload: PlayerCreate, db: Session = Depends(get_db)):
    player = Player(**payload.model_dump())
    db.add(player)
    db.flush()
    _backfill_availability(db, player.id)
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
        password_changed_at=datetime.now(timezone.utc),
    )
    db.add(user)
    db.flush()

    player = Player(user_id=user.id, naam=payload.naam)
    db.add(player)
    db.flush()
    _backfill_availability(db, player.id)
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


@router.put("/{player_id}", response_model=UserOut, dependencies=[Depends(require_beheer)])
def update_player(player_id: int, payload: UserUpdate, db: Session = Depends(get_db)):
    """Wijzig naam/rol/e-mail/actief (en optioneel ontgrendelwachtwoord) van een speler."""
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player or not player.user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Speler niet gevonden")
    user = player.user

    if payload.email is not None and payload.email != user.email:
        if payload.email and db.query(User).filter(User.email == payload.email, User.id != user.id).first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="E-mailadres al in gebruik")
        user.email = payload.email

    if payload.naam is not None:
        user.naam = payload.naam
        player.naam = payload.naam

    new_rol = payload.rol if payload.rol is not None else user.rol
    if new_rol in (UserRole.CAPTAIN, UserRole.BEHEER) and user.rol == UserRole.SPELER and not payload.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ontgrendelwachtwoord is verplicht bij het promoveren naar captain/beheer",
        )
    if payload.rol is not None:
        user.rol = payload.rol

    if payload.actief is not None:
        user.actief = payload.actief

    if payload.password:
        user.hashed_password = hash_password(payload.password)
        user.password_changed_at = datetime.now(timezone.utc)

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


@router.delete("/{player_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_beheer)])
def delete_player(player_id: int, db: Session = Depends(get_db)):
    """Zet een speler op inactief in plaats van 'm echt te verwijderen: een
    hard delete trekt ook alle beschikbaarheid- en opstelling-geschiedenis
    (dus statistieken) van die speler mee weg. Inactief verdwijnt de speler
    uit de naam-kiezer en kan niet meer inloggen, maar de geschiedenis
    blijft gewoon staan — via Beheer > Spelers weer op actief te zetten."""
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player or not player.user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Speler niet gevonden")

    player.user.actief = False
    db.commit()
