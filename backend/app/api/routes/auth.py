from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_beheer, require_captain, require_team_access
from app.core.rate_limit import RateLimiter, client_ip
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
    ChangePasswordRequest,
    EnterRequest,
    LoginRequest,
    TeamAccessRequest,
    Token,
)
from app.schemas.user import UserOut

router = APIRouter(prefix="/auth", tags=["auth"])

# Los per endpoint: dit zijn alle drie wachtwoord-checks die vanaf het
# internet te bereiken zijn zonder dat je al bent ingelogd (team-access is
# de meest kwetsbare — één kort gedeeld wachtwoord, in principe door
# iedereen te gokken zonder rate limit).
_login_limiter = RateLimiter(max_attempts=10, window_seconds=300)
_team_access_limiter = RateLimiter(max_attempts=10, window_seconds=300)
_enter_limiter = RateLimiter(max_attempts=10, window_seconds=300)


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Klassieke e-mail/wachtwoord-login. De app zelf gebruikt de naam-kiezer
    (team-access -> accounts -> enter) hieronder; dit blijft beschikbaar als
    programmatische/backup-ingang met dezelfde wachtwoorden."""
    _login_limiter.check(client_ip(request))
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Onjuiste inloggegevens")
    if not user.actief:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is niet actief")
    token = create_access_token(subject=str(user.id), password_changed_at=user.password_changed_at)
    return Token(access_token=token)


@router.post("/team-access", response_model=Token)
def team_access(payload: TeamAccessRequest, request: Request, db: Session = Depends(get_db)):
    """Stap 1 van de naam-kiezer: het gedeelde teamwachtwoord."""
    _team_access_limiter.check(client_ip(request))
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
def enter(payload: EnterRequest, request: Request, db: Session = Depends(get_db)):
    """Stap 3: naam gekozen. Captain/beheer moet daarbij het persoonlijke
    ontgrendelwachtwoord meesturen; speler niet."""
    _enter_limiter.check(client_ip(request))
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

    return Token(
        access_token=create_access_token(subject=str(user.id), password_changed_at=user.password_changed_at)
    )


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


@router.put("/me/password", dependencies=[Depends(require_captain)])
def change_own_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Captain/beheer wijzigt hier het eigen ontgrendelwachtwoord, zonder
    tussenkomst van Beheer > Spelers."""
    if not verify_password(payload.huidig_wachtwoord, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Huidig wachtwoord is onjuist"
        )
    if not payload.nieuw_wachtwoord:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Nieuw wachtwoord mag niet leeg zijn"
        )
    current_user.hashed_password = hash_password(payload.nieuw_wachtwoord)
    current_user.password_changed_at = datetime.now(timezone.utc)
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
