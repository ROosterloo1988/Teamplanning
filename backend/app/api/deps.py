from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/enter", auto_error=False)

_credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Niet ingelogd of sessie verlopen",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    token: str | None = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    if not token:
        raise _credentials_exception
    payload = decode_token(token)
    if not payload or payload.get("type") != "user":
        raise _credentials_exception
    user = db.query(User).filter(User.email == payload.get("sub")).first()
    if not user or not user.actief:
        raise _credentials_exception
    return user


def require_team_access(token: str | None = Depends(oauth2_scheme)) -> None:
    """Poortwachter voor de naam-kiezer: bewijst dat het gedeelde
    teamwachtwoord is ingevoerd (GET /auth/accounts, POST /auth/enter)."""
    if not token:
        raise _credentials_exception
    payload = decode_token(token)
    if not payload or payload.get("type") != "team":
        raise _credentials_exception


def require_role(*roles: UserRole):
    def _dependency(user: User = Depends(get_current_user)) -> User:
        if user.rol not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Onvoldoende rechten")
        return user

    return _dependency


require_captain = require_role(UserRole.CAPTAIN, UserRole.BEHEER)
require_beheer = require_role(UserRole.BEHEER)
