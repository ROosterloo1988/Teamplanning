from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class TeambeheerConfigUpdate(BaseModel):
    bond_id: int
    poule: str
    team_id: int


class TeambeheerConfigOut(TeambeheerConfigUpdate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    season_id: int
    team_naam: str | None
    last_synced_at: datetime | None
    last_sync_status: str | None
    last_sync_message: str | None


class TeambeheerFixturePreview(BaseModel):
    speelweek: int
    datum: date | None
    datum_raw: str
    thuisteam: str
    uitteam: str
    locatie: str | None = None
    uitslag: str | None = None
    uitslag_url: str | None = None
    status: str  # "nieuw" | "bestaand" | "geen_datum"


class TeambeheerSyncResult(BaseModel):
    created: int
    updated: int
    unchanged: int
    skipped_no_date: int
    team_naam: str | None
