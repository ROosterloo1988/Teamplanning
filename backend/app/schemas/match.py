from datetime import date, time

from pydantic import BaseModel, ConfigDict

from app.models.enums import MatchStatus, MatchType


class MatchBase(BaseModel):
    season_id: int | None = None
    type: MatchType = MatchType.COMPETITIE
    nummer: str | None = None
    datum: date
    tijd: time | None = None
    thuisteam: str
    uitteam: str
    locatie: str | None = None
    status: MatchStatus = MatchStatus.GEPLAND


class MatchCreate(MatchBase):
    external_id: str | None = None


class MatchOut(MatchBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    external_id: str | None = None
