from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.enums import UserRole


class UserBase(BaseModel):
    naam: str
    email: EmailStr
    rol: UserRole = UserRole.SPELER
    actief: bool = True


class UserCreate(UserBase):
    # Alleen verplicht voor CAPTAIN/BEHEER: het ontgrendelwachtwoord voor de
    # naam-kiezer. Voor SPELER wordt er (ongebruikt) automatisch een
    # gegenereerd, want die logt puur in door op zijn naam te klikken.
    password: str | None = None
    team_id: int | None = None


class UserOut(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    player_id: int | None = None
