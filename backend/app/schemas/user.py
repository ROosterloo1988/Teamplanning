from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.enums import UserRole


class UserBase(BaseModel):
    naam: str
    email: EmailStr
    rol: UserRole = UserRole.SPELER
    actief: bool = True


class UserCreate(UserBase):
    password: str
    team_id: int | None = None


class UserOut(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    player_id: int | None = None
