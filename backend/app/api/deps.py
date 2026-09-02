from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def get_current_user(
    token: str | None = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Niet ingelogd of sessie verlopen",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception
    email = decode_access_token(token)
    if not email:
        raise credentials_exception
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.actief:
        raise credentials_exception
    return user


def require_role(*roles: UserRole):
    def _dependency(user: User = Depends(get_current_user)) -> User:
        if user.rol not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Onvoldoende rechten")
        return user

    return _dependency


require_captain = require_role(UserRole.CAPTAIN, UserRole.BEHEER)
require_beheer = require_role(UserRole.BEHEER)
