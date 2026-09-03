from datetime import date
from pathlib import Path

from app.services.teambeheer import parse_jaarprogramma, resolve_year, season_code

FIXTURE = Path(__file__).parent / "fixtures" / "teambeheer_jaarprogramma_1a.html"


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
