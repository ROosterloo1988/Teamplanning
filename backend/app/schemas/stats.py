from pydantic import BaseModel


class PlayerStatsOut(BaseModel):
    player_id: int
    player_naam: str
    totaal: int
    beschikbaar: int
    niet_beschikbaar: int
    indien_nodig: int
    geen_antwoord: int
    response_rate: float  # percentage van wedstrijden met een antwoord (0-100)
    keer_opgesteld: int
