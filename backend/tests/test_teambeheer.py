from datetime import date
from pathlib import Path

from app.services.teambeheer import (
    parse_speelgelegenheden,
    parse_team_page,
    parse_teams,
    resolve_team_date,
    season_code,
)

TEAM_FIXTURE = Path(__file__).parent / "fixtures" / "teambeheer_team_3852.html"
SPEELGELEGENHEDEN_FIXTURE = Path(__file__).parent / "fixtures" / "teambeheer_speelgelegenheden.html"
TEAMS_FIXTURE = Path(__file__).parent / "fixtures" / "teambeheer_teams.html"


def _fixtures():
    return parse_team_page(TEAM_FIXTURE.read_text())


def test_parse_reads_only_computer_section_rows():
    # De tablet- en mobiel-secties herhalen wedstrijd 1 nog een keer (zonder
    # de `title`-id) — die mogen niet meegeteld worden, anders telt alles
    # drievoudig.
    assert len(_fixtures()) == 16


def test_parse_skips_vrije_week():
    fixtures = _fixtures()
    assert all(f.official_id != 3305772 for f in fixtures)
    assert all(f.datum_raw != "Vrije week" for f in fixtures)


def test_parse_flags_beker_rows():
    fixtures = _fixtures()
    beker = [f for f in fixtures if f.is_beker]
    assert {f.official_id for f in beker} == {3386239}

    cup_match = beker[0]
    assert cup_match.ronde == "b2"
    assert cup_match.datum_raw == "22-10-2026"
    assert cup_match.thuis_naam.strip() == "DE GOUV"
    assert cup_match.uit_naam == "Lange nie bes't"
    assert cup_match.score == "8-1"
    assert (
        cup_match.score_url
        == "https://feeds.teambeheer.nl/web/wedstrijdformulier/?d=11&w=3386239&s=26-27"
    )


def test_parse_competitie_rows_not_flagged_as_beker():
    fixtures = _fixtures()
    assert all(not f.is_beker for f in fixtures if f.ronde.isdigit())


def test_parse_official_id_and_teams_from_first_row():
    row = next(f for f in _fixtures() if f.official_id == 3135390)
    assert row.ronde == "1"
    assert row.datum_raw == "02-09-2026"
    assert row.thuis_naam == "Het Praothuus 2"
    assert row.thuis_id == 3854
    assert row.uit_naam.strip() == "DE GOUV"
    assert row.uit_id == 3852
    assert row.score == "3-6"
    assert (
        row.score_url == "https://feeds.teambeheer.nl/web/wedstrijdformulier/?d=11&w=3135390&s=26-27"
    )


def test_parse_unconfirmed_score_is_plain_text_without_link():
    row = next(f for f in _fixtures() if f.official_id == 3135432)
    assert row.score == "6-"
    assert row.score_url is None


def test_parse_empty_score_for_future_match():
    row = next(f for f in _fixtures() if f.official_id == 3135439)
    assert row.score == ""
    assert row.score_url is None


def test_resolve_team_date_parses_full_dd_mm_yyyy():
    assert resolve_team_date("02-09-2026") == date(2026, 9, 2)
    assert resolve_team_date("20-05-2027") == date(2027, 5, 20)


def test_resolve_team_date_returns_none_for_unknown_date():
    assert resolve_team_date("Vrije week") is None
    assert resolve_team_date("n.n.b.") is None
    assert resolve_team_date("") is None


def test_season_code_format():
    assert season_code(2026) == "26-27"
    assert season_code(2099) == "99-00"


def test_parse_speelgelegenheden():
    venues = parse_speelgelegenheden(SPEELGELEGENHEDEN_FIXTURE.read_text())
    assert len(venues) == 15

    gouverneur = venues[19]
    assert gouverneur.naam == "Café de Gouverneur"
    assert gouverneur.adres == "Munstersestraat 2"
    assert gouverneur.plaats == "Raalte"
    assert gouverneur.volledig_adres == "Munstersestraat 2, Raalte"
    assert gouverneur.label == "Café de Gouverneur, Munstersestraat 2, Raalte"


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
    assert addresses[3852] == "Café de Gouverneur, Munstersestraat 2, Raalte"  # DE GOUV
    assert addresses[3854] == "Het Praothuus, Langstraat 44, Wijhe"  # Het Praothuus 2


def test_team_venue_addresses_degrades_gracefully_on_fetch_error(monkeypatch):
    from app.services import teambeheer as teambeheer_module

    def _raise(bond_id, s_code):
        raise teambeheer_module.TeambeheerFetchError("kapot")

    monkeypatch.setattr(teambeheer_module, "fetch_teams", _raise)
    assert teambeheer_module.team_venue_addresses(11, "26-27") == {}
