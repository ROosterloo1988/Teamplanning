from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str) -> str:
    """Normaal gebruikerstoken: subject is het e-mailadres van de user."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": subject, "type": "user", "exp": expire}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_team_token() -> str:
    """Teamtoegangstoken: bewijst dat het gedeelde teamwachtwoord is ingevoerd,
    beschermt de naam-kiezer (GET /auth/accounts, POST /auth/enter) maar geeft
    geen toegang tot verder beveiligde routes.
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.TEAM_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": "team", "type": "team", "exp": expire}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
