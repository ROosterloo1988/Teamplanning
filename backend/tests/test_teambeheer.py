from datetime import date
from pathlib import Path

from app.services.teambeheer import (
    parse_jaarprogramma,
    parse_speelgelegenheden,
    parse_teams,
    resolve_year,
    season_code,
)

FIXTURE = Path(__file__).parent / "fixtures" / "teambeheer_jaarprogramma_1a.html"
FULL_SEASON_FIXTURE = Path(__file__).parent / "fixtures" / "teambeheer_jaarprogramma_1a_full_season.html"
SPEELGELEGENHEDEN_FIXTURE = Path(__file__).parent / "fixtures" / "teambeheer_speelgelegenheden.html"
TEAMS_FIXTURE = Path(__file__).parent / "fixtures" / "teambeheer_teams.html"


def _fixtures():
    html = FIXTURE.read_text()
    return parse_jaarprogramma(html)


def test_parse_finds_three_speelweken():
    fixtures = _fixtures()
    assert {f.speelweek for f in fixtures} == {1, 2, 3}


def test_parse_speelweek_1_row_count_and_score():
    fixtures = [f for f in _fixtures() if f.speelweek == 1]
    assert len(fixtures) == 7
    mila_row = next(f for f in fixtures if f.thuis_naam == "MILA B")
    assert mila_row.uit_naam == "Woodpeckers 1"
    assert mila_row.score == "-7"
    assert mila_row.score_url is None  # plat tekst-scorecel, geen wedstrijdformulier-link


def test_parse_score_url_from_wedstrijdformulier_link():
    """Een afgehandelde wedstrijd heeft een score-cel die naar het officiele
    wedstrijdformulier linkt (/web/wedstrijdformulier/?d=&w=&s=), niet zomaar
    platte tekst."""
    fixtures = [f for f in parse_jaarprogramma(FULL_SEASON_FIXTURE.read_text()) if f.speelweek == 1]
    linked_row = next(f for f in fixtures if f.thuis_naam == "Mansier Zittie?")
    assert linked_row.score == "7-2"
    assert linked_row.score_url == "https://feeds.teambeheer.nl/web/wedstrijdformulier/?d=11&w=3135387&s=26-27"


def test_de_gouv_appears_as_thuis_and_uit():
    fixtures = _fixtures()
    de_gouv = [f for f in fixtures if f.thuis_id == 3852 or f.uit_id == 3852]
    assert len(de_gouv) == 3  # once per speelweek in the fixture

    week1 = next(f for f in de_gouv if f.speelweek == 1)
    assert week1.thuis_naam == "Het Praothuus 2"
    assert week1.thuis_id == 3854
    assert week1.uit_naam.strip() == "DE GOUV"
    assert week1.uit_id == 3852

    week2 = next(f for f in de_gouv if f.speelweek == 2)
    assert week2.thuis_naam.strip() == "DE GOUV"
    assert week2.uit_naam == "MILA B"

    week3 = next(f for f in de_gouv if f.speelweek == 3)
    assert week3.thuis_naam == "Woodpeckers 1"
    assert week3.uit_naam.strip() == "DE GOUV"


def test_nnb_date_is_preserved_raw():
    fixtures = [f for f in _fixtures() if f.speelweek == 2]
    kokkis_row = next(f for f in fixtures if f.thuis_naam == "Kokki's Café")
    assert kokkis_row.datum_raw == "n.n.b."


def test_resolve_year_splits_on_season_boundary():
    # Seizoen 2026-2027: juli t/m december -> startjaar, januari t/m juni -> eindjaar.
    assert resolve_year("02-09", 2026, 2027) == date(2026, 9, 2)
    assert resolve_year("14-01", 2026, 2027) == date(2027, 1, 14)


def test_resolve_year_returns_none_for_unknown_date():
    assert resolve_year("n.n.b.", 2026, 2027) is None
    assert resolve_year("", 2026, 2027) is None


def test_season_code_format():
    assert season_code(2026) == "26-27"
    assert season_code(2099) == "99-00"


def test_de_gouv_jan_to_may_dates_resolve_into_next_calendar_year():
    """Regressietest tegen een echte, volledige jaarprogramma-pagina (speelweek
    1 t/m 26): rond de jaarwisseling staat er op de feed nog steeds gewoon
    'DD-MM' (bv. '07-01'), zonder jaartal. resolve_year moet die met de
    seizoensgrens (juli t/m december -> startjaar, januari t/m juni ->
    eindjaar) naar het juiste kalenderjaar 2027 omzetten, niet als
    'geen datum' (n.n.b.) behandelen."""
    html = FULL_SEASON_FIXTURE.read_text()
    fixtures = [f for f in parse_jaarprogramma(html) if f.thuis_id == 3852 or f.uit_id == 3852]
    assert len(fixtures) == 26  # DE GOUV speelt elke speelweek van 1 t/m 26

    resolved = {f.speelweek: resolve_year(f.datum_raw, 2026, 2027) for f in fixtures}
    assert None not in resolved.values()

    # Voorbeelden na de jaarwisseling: allemaal 2027, oplopend met de speelweek.
    assert resolved[13] == date(2027, 1, 7)
    assert resolved[14] == date(2027, 1, 14)
    assert resolved[15] == date(2027, 1, 20)
    assert resolved[18] == date(2027, 2, 24)
    assert resolved[26] == date(2027, 5, 20)

    # ... en de eerste seizoenshelft blijft gewoon 2026.
    assert resolved[1] == date(2026, 9, 2)
    assert resolved[12] == date(2026, 12, 10)

    # De reeks moet chronologisch oplopen (geen datum "voor" de vorige speelweek).
    ordered = [resolved[week] for week in sorted(resolved)]
    assert ordered == sorted(ordered)


def test_parse_speelgelegenheden():
    venues = parse_speelgelegenheden(SPEELGELEGENHEDEN_FIXTURE.read_text())
    assert len(venues) == 15

    gouverneur = venues[19]
    assert gouverneur.naam == "Café de Gouverneur"
    assert gouverneur.adres == "Munstersestraat 2"
    assert gouverneur.plaats == "Raalte"
    assert gouverneur.volledig_adres == "Munstersestraat 2, Raalte"


def test_parse_teams():
    team_venue = parse_teams(TEAMS_FIXTURE.read_text())
    assert len(team_venue) == 14
    assert team_venue[3852] == 19  # DE GOUV -> Café de Gouverneur


def test_team_venue_addresses_combines_both_feeds(monkeypatch):
    from app.services import teambeheer as teambeheer_module

    monkeypatch.setattr(
        teambeheer_module, "fetch_teams", lambda bond_id, s_code: TEAMS_FIXTURE.read_text()
    )
    monkeypatch.setattr(
        teambeheer_module,
        "fetch_speelgelegenheden",
        lambda bond_id, s_code: SPEELGELEGENHEDEN_FIXTURE.read_text(),
    )

    addresses = teambeheer_module.team_venue_addresses(11, "26-27")
    assert addresses[3852] == "Munstersestraat 2, Raalte"  # DE GOUV
    assert addresses[3854] == "Langstraat 44, Wijhe"  # Het Praothuus 2


def test_team_venue_addresses_degrades_gracefully_on_fetch_error(monkeypatch):
    from app.services import teambeheer as teambeheer_module

    def _raise(bond_id, s_code):
        raise teambeheer_module.TeambeheerFetchError("kapot")

    monkeypatch.setattr(teambeheer_module, "fetch_teams", _raise)
    assert teambeheer_module.team_venue_addresses(11, "26-27") == {}
