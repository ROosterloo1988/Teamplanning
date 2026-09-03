from datetime import date, datetime

from pydantic import BaseModel


class AuditLogOut(BaseModel):
    id: int
    created_at: datetime
    user_naam: str | None
    entity_type: str
    action: str
    old_value: str | None
    new_value: str | None
    match_id: int | None = None
    match_datum: date | None = None
    match_thuisteam: str | None = None
    match_uitteam: str | None = None
    player_naam: str | None = None
