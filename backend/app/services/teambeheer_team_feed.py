"""Experimentele (beta) import vanaf de Teambeheer SDC team-feed.

Dit is een los, niet-destructief diagnosepad naast de bestaande,
jaarprogramma-gebaseerde sync in `app/services/teambeheer.py`. Doel:
uitzoeken of/hoe `https://feeds.teambeheer.nl/web/team?d=<bond>&t=<team>&s=<seizoen>`
— die wél bekerwedstrijden toont — live werkt, zonder de bestaande,
werkende sync aan te raken. Schrijft nooit naar de database; alleen lezen
en tonen. Pas als dit op de echte server betrouwbaar wedstrijden teruggeeft,
voegen we het samen met de echte sync.

De feed toont, in het "computer"-blok, één tabel "Wedstrijden" met alle
wedstrijden van dit ene team (competitie én beker door elkaar). Elke rij
heeft een `title`-attribuut met Teambeheer's eigen, wereldwijd unieke
wedstrijd-id. Bekerrondes hebben een rondenummer dat met "b" begint
(bv. "b1", "b2"); een "Vrije week" (bye) heeft geen tegenstander-link.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date

import httpx
from bs4 import BeautifulSoup

from app.core.config import settings
from app.services.teambeheer import TeambeheerFetchError, _team_id_from_href

TEAM_DATUM_RE = re.compile(r"^(\d{2})-(\d{2})-(\d{4})$")


@dataclass
class TeamFixture:
    official_id: int
    ronde: str
    is_beker: bool
    datum_raw: str
    thuis_id: int
    thuis_naam: str
    uit_id: int
    uit_naam: str
    score: str
    score_url: str | None = None


@dataclass
class TeamFeedDiagnostics:
    url: str
    html_length: int = 0
    computer_section_found: bool = False
    wedstrijden_header_found: bool = False
    table_found: bool = False
    tbody_found: bool = False
    raw_row_count: int = 0
    skipped_no_title: int = 0
    skipped_vrije_week: int = 0
    parsed_count: int = 0
    error: str | None = None
    fixtures: list[TeamFixture] = field(default_factory=list)


def resolve_team_date(datum_raw: str) -> date | None:
    """'02-09-2026' -> 2026-09-02. Alles zonder dat volledige dd-mm-jjjj-
    formaat (bv. 'n.n.b.', 'Vrije week') betekent: (nog) geen bekende datum."""
    match = TEAM_DATUM_RE.match(datum_raw.strip())
    if not match:
        return None
    day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
    try:
        return date(year, month, day)
    except ValueError:
        return None


def fetch_team_page(bond_id: int, s_code: str, team_id: int) -> str:
    url = f"{settings.TEAMBEHEER_BASE_URL}/web/team"
    try:
        response = httpx.get(
            url,
            params={"d": bond_id, "s": s_code, "t": team_id},
            timeout=20,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; TeamplanningSync/1.0)"},
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise TeambeheerFetchError(f"Kon Teambeheer niet bereiken: {exc}") from exc
    return response.text


def parse_team_page(html: str, diag: TeamFeedDiagnostics) -> list[TeamFixture]:
    """Vult `diag` stap voor stap terwijl 'm geparst wordt, zodat je op de
    echte server meteen ziet bij welke stap het misgaat als er 0 wedstrijden
    uitkomen (bv. het "computer"-blok niet gevonden, of de tabel wel
    gevonden maar alle rijen overgeslagen)."""
    diag.html_length = len(html)
    soup = BeautifulSoup(html, "html.parser")

    computer_section = soup.find("div", class_="computer")
    if not computer_section:
        return []
    diag.computer_section_found = True

    header = computer_section.find("h2", string=lambda s: bool(s) and "Wedstrijden" in s)
    if not header:
        return []
    diag.wedstrijden_header_found = True

    table = header.find_next("table")
    if not table:
        return []
    diag.table_found = True

    tbody = table.find("tbody")
    if not tbody:
        return []
    diag.tbody_found = True

    rows = tbody.find_all("tr", recursive=False)
    diag.raw_row_count = len(rows)

    fixtures: list[TeamFixture] = []
    for row in rows:
        cells = row.find_all("td", recursive=False)
        if len(cells) < 4:
            continue

        official_id_raw = cells[0].get("title")
        if not official_id_raw:
            diag.skipped_no_title += 1
            continue
        try:
            official_id = int(official_id_raw)
        except ValueError:
            diag.skipped_no_title += 1
            continue
        ronde = cells[0].get_text(strip=True)

        datum_raw = cells[1].get_text(strip=True)
        thuis_a = cells[2].find("a")
        uit_a = cells[3].find("a")
        if not thuis_a or not uit_a:
            diag.skipped_vrije_week += 1
            continue
        thuis_id = _team_id_from_href(thuis_a.get("href", ""))
        uit_id = _team_id_from_href(uit_a.get("href", ""))
        if thuis_id is None or uit_id is None:
            diag.skipped_vrije_week += 1
            continue

        score_cell = cells[4] if len(cells) > 4 else None
        score_a = score_cell.find("a") if score_cell else None
        if score_a:
            score = score_a.get_text(strip=True)
            score_url = (
                f"{settings.TEAMBEHEER_BASE_URL}{score_a['href']}" if score_a.get("href") else None
            )
        else:
            score = score_cell.get_text(strip=True) if score_cell else ""
            score_url = None

        fixtures.append(
            TeamFixture(
                official_id=official_id,
                ronde=ronde,
                is_beker=ronde.lower().startswith("b"),
                datum_raw=datum_raw,
                thuis_id=thuis_id,
                thuis_naam=thuis_a.get_text(strip=True),
                uit_id=uit_id,
                uit_naam=uit_a.get_text(strip=True),
                score=score,
                score_url=score_url,
            )
        )

    diag.parsed_count = len(fixtures)
    return fixtures


def diagnose_team_feed(bond_id: int, team_id: int, s_code: str) -> TeamFeedDiagnostics:
    """Haalt de team-feed op en parst 'm, zonder iets op te slaan. Geeft bij
    een fetch- of parsefout nooit een exception, maar een diagnostics-object
    met `error` gezet — zo blijft dit knopje altijd bruikbaar om te zien
    wat er precies misgaat op de echte server."""
    url = f"{settings.TEAMBEHEER_BASE_URL}/web/team?d={bond_id}&t={team_id}&s={s_code}"
    diag = TeamFeedDiagnostics(url=url)
    try:
        html = fetch_team_page(bond_id, s_code, team_id)
    except TeambeheerFetchError as exc:
        diag.error = str(exc)
        return diag

    fixtures = parse_team_page(html, diag)
    diag.fixtures = fixtures
    return diag
