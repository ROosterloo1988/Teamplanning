from pydantic import BaseModel

from app.schemas.match import MatchOut


class MatchReminderOut(BaseModel):
    match: MatchOut
    total: int
    missing: int
