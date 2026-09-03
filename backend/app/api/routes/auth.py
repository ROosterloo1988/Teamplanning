from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_beheer, require_team_access
from app.core.security import (
    create_access_token,
    create_team_token,
    hash_password,
    verify_password,
)
from app.db.session import get_db
from app.models.app_setting import AppSetting
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.auth import (
    AccountOption,
    EnterRequest,
    LoginRequest,
    TeamAccessRequest,
    Token,
)
from app.schemas.user import UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """Klassieke e-mail/wachtwoord-login. De app zelf gebruikt de naam-kiezer
    (team-access -> accounts -> enter) hieronder; dit blijft beschikbaar als
    programmatische/backup-ingang met dezelfde wachtwoorden."""
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Onjuiste inloggegevens")
    if not user.actief:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is niet actief")
    token = create_access_token(subject=user.email)
    return Token(access_token=token)


@router.post("/team-access", response_model=Token)
def team_access(payload: TeamAccessRequest, db: Session = Depends(get_db)):
    """Stap 1 van de naam-kiezer: het gedeelde teamwachtwoord."""
    setting = db.query(AppSetting).first()
    if not setting or not verify_password(payload.password, setting.team_password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Onjuist teamwachtwoord")
    return Token(access_token=create_team_token())


@router.get(
    "/accounts", response_model=list[AccountOption], dependencies=[Depends(require_team_access)]
)
def list_accounts(db: Session = Depends(get_db)):
    """Stap 2: 'Ik ben: [naam]' — alle actieve accounts."""
    users = db.query(User).filter(User.actief.is_(True)).order_by(User.naam).all()
    return [AccountOption(id=u.id, naam=u.naam, rol=u.rol) for u in users]


@router.post(
    "/enter", response_model=Token, dependencies=[Depends(require_team_access)]
)
def enter(payload: EnterRequest, db: Session = Depends(get_db)):
    """Stap 3: naam gekozen. Captain/beheer moet daarbij het persoonlijke
    ontgrendelwachtwoord meesturen; speler niet."""
    user = db.query(User).filter(User.id == payload.user_id, User.actief.is_(True)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account niet gevonden")

    if user.rol in (UserRole.CAPTAIN, UserRole.BEHEER):
        if not payload.unlock_password or not verify_password(
            payload.unlock_password, user.hashed_password
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Onjuist ontgrendelwachtwoord"
            )

    return Token(access_token=create_access_token(subject=user.email))


@router.put("/team-password", dependencies=[Depends(require_beheer)])
def update_team_password(payload: TeamAccessRequest, db: Session = Depends(get_db)):
    """Wijzig het gedeelde teamwachtwoord (Beheer > Instellingen)."""
    setting = db.query(AppSetting).first()
    if not setting:
        setting = AppSetting(team_password_hash=hash_password(payload.password))
        db.add(setting)
    else:
        setting.team_password_hash = hash_password(payload.password)
    db.commit()
    return {"status": "ok"}


@router.get("/me", response_model=UserOut)
def read_me(current_user: User = Depends(get_current_user)):
    return UserOut(
        id=current_user.id,
        naam=current_user.naam,
        email=current_user.email,
        rol=current_user.rol,
        actief=current_user.actief,
        player_id=current_user.player.id if current_user.player else None,
    )
