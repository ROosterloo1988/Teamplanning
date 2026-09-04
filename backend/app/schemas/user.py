from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.enums import UserRole


class UserBase(BaseModel):
    naam: str
    email: EmailStr | None = None
    rol: UserRole = UserRole.SPELER
    actief: bool = True


class UserCreate(UserBase):
    # Alleen verplicht voor CAPTAIN/BEHEER: het ontgrendelwachtwoord voor de
    # naam-kiezer. Voor SPELER wordt er (ongebruikt) automatisch een
    # gegenereerd, want die logt puur in door op zijn naam te klikken.
    password: str | None = None


class UserUpdate(BaseModel):
    naam: str | None = None
    email: EmailStr | None = None
    rol: UserRole | None = None
    actief: bool | None = None
    # Alleen invullen om het ontgrendelwachtwoord te (laten) wijzigen; verplicht
    # bij het promoveren van SPELER naar CAPTAIN/BEHEER (die heeft er nog geen).
    password: str | None = None


class UserOut(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    player_id: int | None = None
