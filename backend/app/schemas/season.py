from pydantic import BaseModel, ConfigDict


class SeasonBase(BaseModel):
    naam: str
    startjaar: int
    eindjaar: int


class SeasonCreate(BaseModel):
    naam: str
    startjaar: int
    # eindjaar is altijd startjaar + 1 (een seizoen loopt van zomer tot zomer) —
    # niet apart invoerbaar, dat gaf ruimte voor een verkeerd getal dat
    # resolve_year() liet crashen op wedstrijden na de jaarwisseling.


class SeasonOut(SeasonBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    actief: bool
    # Doorlink naar de Teambeheer-standenpagina voor dit seizoen (zelfde
    # opzet als uitslag_url naar het wedstrijdformulier) — None als er nog
    # geen Teambeheer-koppeling is ingesteld.
    stand_url: str | None = None
