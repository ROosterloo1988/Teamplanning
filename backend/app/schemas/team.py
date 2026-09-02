from pydantic import BaseModel, ConfigDict


class TeamBase(BaseModel):
    naam: str
    vereniging: str | None = None


class TeamCreate(TeamBase):
    pass


class TeamOut(TeamBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
