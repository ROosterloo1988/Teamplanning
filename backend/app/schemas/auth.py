from pydantic import BaseModel, EmailStr

from app.models.enums import UserRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TeamAccessRequest(BaseModel):
    password: str


class AccountOption(BaseModel):
    id: int
    naam: str
    rol: UserRole


class EnterRequest(BaseModel):
    user_id: int
    unlock_password: str | None = None
