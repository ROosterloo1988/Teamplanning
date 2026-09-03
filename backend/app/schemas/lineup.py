from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LineupUpdate(BaseModel):
    player_ids: list[int]


class LineupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    match_id: int
    published: bool
    published_at: datetime | None
    player_ids: list[int]
    player_naam: list[str] = []
