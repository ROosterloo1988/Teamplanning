from pydantic import BaseModel, ConfigDict


class SeasonBase(BaseModel):
    naam: str
    startjaar: int
    eindjaar: int


class SeasonCreate(SeasonBase):
    pass


class SeasonOut(SeasonBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    actief: bool
