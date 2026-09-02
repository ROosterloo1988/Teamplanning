from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import AvailabilityStatus


class AvailabilityUpdate(BaseModel):
    status: AvailabilityStatus


class AvailabilityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    match_id: int
    player_id: int
    status: AvailabilityStatus
    updated_at: datetime


class AvailabilityWithPlayer(AvailabilityOut):
    player_naam: str
