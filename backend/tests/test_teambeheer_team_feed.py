from datetime import date
from pathlib import Path

from app.services.teambeheer_team_feed import (
    TeamFeedDiagnostics,
    diagnose_team_feed,
    parse_team_page,
    resolve_team_date,
)

TEAM_FIXTURE = Path(__file__).parent / "fixtures" / "teambeheer_team_3852.html"


def _parse():
    diag = TeamFeedDiagnostics(url="https://example.invalid")
    fixtures = parse_team_page(TEAM_FIXTURE.read_text(), diag)
    return fixtures, diag


def test_parse_reads_only_computer_section_rows():
    # De tablet- en mobiel-secties herhalen wedstrijd 1 nog een keer (zonder
    # de `title`-id) — die mogen niet meegeteld worden, anders telt alles
    # drievoudig.
    fixtures, diag = _parse()
    assert len(fixtures) == 16
    assert diag.parsed_count == 16


def test_diagnostics_track_each_parse_stage():
    _, diag = _parse()
    assert diag.computer_section_found is True
    assert diag.wedstrijden_header_found is True
    assert diag.table_found is True
    assert diag.tbody_found is True
    assert diag.raw_row_count == 18  # 16 echte + 1 bye + 1 lege afsluit-rij (geen <td>'s)
    assert diag.skipped_vrije_week == 1
    assert diag.skipped_no_title == 0


def test_parse_skips_vrije_week():
    fixtures, _ = _parse()
    assert all(f.official_id != 3305772 for f in fixtures)
    assert all(f.datum_raw != "Vrije week" for f in fixtures)


def test_parse_flags_beker_rows():
    fixtures, _ = _parse()
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
    fixtures, _ = _parse()
    assert all(not f.is_beker for f in fixtures if f.ronde.isdigit())


def test_parse_official_id_and_teams_from_first_row():
    fixtures, _ = _parse()
    row = next(f for f in fixtures if f.official_id == 3135390)
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
    fixtures, _ = _parse()
    row = next(f for f in fixtures if f.official_id == 3135432)
    assert row.score == "6-"
    assert row.score_url is None


def test_resolve_team_date_parses_full_dd_mm_yyyy():
    assert resolve_team_date("02-09-2026") == date(2026, 9, 2)
    assert resolve_team_date("20-05-2027") == date(2027, 5, 20)


def test_resolve_team_date_returns_none_for_unknown_date():
    assert resolve_team_date("Vrije week") is None
    assert resolve_team_date("n.n.b.") is None
    assert resolve_team_date("") is None


def test_diagnose_team_feed_sets_error_on_fetch_failure(monkeypatch):
    from app.services import teambeheer_team_feed as module
    from app.services.teambeheer import TeambeheerFetchError

    def _raise(bond_id, s_code, team_id):
        raise TeambeheerFetchError("kapot")

    monkeypatch.setattr(module, "fetch_team_page", _raise)
    diag = diagnose_team_feed(11, 3852, "26-27")
    assert diag.error == "kapot"
    assert diag.fixtures == []
    assert diag.computer_section_found is False


def test_diagnose_team_feed_happy_path(monkeypatch):
    from app.services import teambeheer_team_feed as module

    monkeypatch.setattr(
        module, "fetch_team_page", lambda bond_id, s_code, team_id: TEAM_FIXTURE.read_text()
    )
    diag = diagnose_team_feed(11, 3852, "26-27")
    assert diag.error is None
    assert diag.parsed_count == 16
    assert diag.url == "https://feeds.teambeheer.nl/web/team?d=11&t=3852&s=26-27"
