from pydantic import BaseModel, ConfigDict


class PlayerBase(BaseModel):
    naam: str


class PlayerCreate(PlayerBase):
    user_id: int | None = None


class PlayerOut(PlayerBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None = None
