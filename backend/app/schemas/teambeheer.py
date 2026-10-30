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


class TeamFeedFixturePreview(BaseModel):
    """Beta: voorbeeld van een wedstrijd zoals geparst uit de nieuwe
    /web/team-feed (die ook bekerwedstrijden toont)."""

    official_id: int
    ronde: str
    is_beker: bool
    datum: date | None
    datum_raw: str
    thuisteam: str
    uitteam: str
    uitslag: str | None = None
    uitslag_url: str | None = None


class TeamFeedDiagnosticsOut(BaseModel):
    """Beta: diagnose van het ophalen/parsen van de /web/team-feed, zodat je
    op de echte server meteen ziet bij welke stap het misgaat als er 0
    wedstrijden uitkomen."""

    url: str
    html_length: int
    computer_section_found: bool
    computer_sections_count: int
    wedstrijden_header_found: bool
    table_found: bool
    tbody_found: bool
    raw_row_count: int
    skipped_no_title: int
    skipped_vrije_week: int
    parsed_count: int
    error: str | None = None
    headers_seen: list[str] = []
    fixtures: list[TeamFeedFixturePreview]
