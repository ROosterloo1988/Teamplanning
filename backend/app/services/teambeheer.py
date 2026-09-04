"""Import van de Teambeheer SDC jaarprogramma-feed.

De feed (https://feeds.teambeheer.nl/web/jaarprogramma?d=<bond>&s=<seizoen>&div=<poule>)
is geen data-API maar een Semantic-UI HTML-pagina: per speelweek een
<div class="column"> met een <h4>Speelweek N</h4> en een tabel met kolommen
Datum / Thuisteam / Uitteam / Score. Team-namen zijn links naar
/web/team?d=<bond>&t=<teamnummer>&s=<seizoen> — dat teamnummer is de enige
stabiele identifier van een team en wordt gebruikt om "onze" wedstrijden uit
de poule te filteren. Zie functioneel ontwerp v1 secties 6 en 7.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from urllib.parse import parse_qs, urlparse

import httpx
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.availability import Availability
from app.models.enums import AvailabilityStatus, MatchStatus, MatchType
from app.models.match import Match
from app.models.player import Player
from app.models.season import Season
from app.models.teambeheer import TeambeheerConfig
from app.services.notifications import notify_all_players

SPEELWEEK_RE = re.compile(r"Speelweek\s+(\d+)", re.IGNORECASE)
DATUM_RE = re.compile(r"^(\d{2})-(\d{2})$")


class TeambeheerFetchError(Exception):
    """De jaarprogramma-pagina kon niet opgehaald of gelezen worden."""


@dataclass
class TeambeheerFixture:
    speelweek: int
    datum_raw: str
    thuis_id: int
    thuis_naam: str
    uit_id: int
    uit_naam: str
    score: str


@dataclass
class Venue:
    """Een speelgelegenheid uit /web/speelgelegenheden — cn is de enige
    stabiele identifier (zit ook in de speelgelegenheid-link op /web/teams)."""

    cn: int
    naam: str
    adres: str
    plaats: str

    @property
    def volledig_adres(self) -> str:
        parts = [p.strip() for p in (self.adres, self.plaats) if p and p.strip()]
        return ", ".join(parts)


def season_code(startjaar: int) -> str:
    """2026 -> '26-27', zoals gebruikt in de s=-queryparameter."""
    return f"{startjaar % 100:02d}-{(startjaar + 1) % 100:02d}"


def resolve_year(datum_raw: str, startjaar: int, eindjaar: int) -> date | None:
    """'02-09' + seizoen 2026-2027 -> 2026-09-02. 'n.n.b.' of onbekend -> None."""
    match = DATUM_RE.match(datum_raw.strip())
    if not match:
        return None
    day, month = int(match.group(1)), int(match.group(2))
    year = startjaar if month >= 7 else eindjaar
    try:
        return date(year, month, day)
    except ValueError:
        return None


def _team_id_from_href(href: str) -> int | None:
    query = parse_qs(urlparse(href).query)
    values = query.get("t")
    if not values:
        return None
    try:
        return int(values[0])
    except ValueError:
        return None


def _venue_cn_from_href(href: str) -> int | None:
    query = parse_qs(urlparse(href).query)
    values = query.get("cn")
    if not values:
        return None
    try:
        return int(values[0])
    except ValueError:
        return None


def _fetch_page(path: str, params: dict) -> str:
    url = f"{settings.TEAMBEHEER_BASE_URL}{path}"
    try:
        response = httpx.get(
            url,
            params=params,
            timeout=20,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; TeamplanningSync/1.0)"},
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise TeambeheerFetchError(f"Kon Teambeheer niet bereiken: {exc}") from exc
    return response.text


def fetch_jaarprogramma(bond_id: int, s_code: str, poule: str) -> str:
    return _fetch_page("/web/jaarprogramma", {"d": bond_id, "s": s_code, "div": poule})


def fetch_speelgelegenheden(bond_id: int, s_code: str) -> str:
    return _fetch_page("/web/speelgelegenheden", {"d": bond_id, "s": s_code})


def fetch_teams(bond_id: int, s_code: str) -> str:
    return _fetch_page("/web/teams", {"d": bond_id, "s": s_code})


def parse_jaarprogramma(html: str) -> list[TeambeheerFixture]:
    soup = BeautifulSoup(html, "html.parser")
    fixtures: list[TeambeheerFixture] = []

    for table in soup.find_all("table"):
        classes = table.get("class") or []
        if "unstackable" not in classes:
            continue

        parent = table.find_parent("div", class_="column")
        header = parent.find("h4") if parent else table.find_previous("h4")
        if not header:
            continue
        week_match = SPEELWEEK_RE.search(header.get_text(strip=True))
        if not week_match:
            continue
        speelweek = int(week_match.group(1))

        tbody = table.find("tbody")
        if not tbody:
            continue

        for row in tbody.find_all("tr", recursive=False):
            cells = row.find_all("td", recursive=False)
            if len(cells) < 3:
                continue

            datum_raw = cells[0].get_text(strip=True)
            thuis_a = cells[1].find("a")
            uit_a = cells[2].find("a")
            if not thuis_a or not uit_a:
                continue
            thuis_id = _team_id_from_href(thuis_a.get("href", ""))
            uit_id = _team_id_from_href(uit_a.get("href", ""))
            if thuis_id is None or uit_id is None:
                continue
            score = cells[3].get_text(strip=True) if len(cells) > 3 else ""

            fixtures.append(
                TeambeheerFixture(
                    speelweek=speelweek,
                    datum_raw=datum_raw,
                    thuis_id=thuis_id,
                    thuis_naam=thuis_a.get_text(strip=True),
                    uit_id=uit_id,
                    uit_naam=uit_a.get_text(strip=True),
                    score=score,
                )
            )

    return fixtures


def parse_speelgelegenheden(html: str) -> dict[int, Venue]:
    """/web/speelgelegenheden -> cn -> Venue (naam, adres, plaats)."""
    soup = BeautifulSoup(html, "html.parser")
    venues: dict[int, Venue] = {}

    table = soup.find("table", id="datatable-l")
    tbody = table.find("tbody") if table else None
    if not tbody:
        return venues

    for row in tbody.find_all("tr", recursive=False):
        cells = row.find_all("td", recursive=False)
        if len(cells) < 3:
            continue
        link = cells[0].find("a")
        if not link:
            continue
        cn = _venue_cn_from_href(link.get("href", ""))
        if cn is None:
            continue
        venues[cn] = Venue(
            cn=cn,
            naam=link.get_text(strip=True),
            adres=cells[1].get_text(strip=True),
            plaats=cells[2].get_text(strip=True),
        )
    return venues


def parse_teams(html: str) -> dict[int, int]:
    """/web/teams -> team-id (t=) -> speelgelegenheid-cn (cn=)."""
    soup = BeautifulSoup(html, "html.parser")
    team_venue: dict[int, int] = {}

    table = soup.find("table", id="datatable-l")
    tbody = table.find("tbody") if table else None
    if not tbody:
        return team_venue

    for row in tbody.find_all("tr", recursive=False):
        cells = row.find_all("td", recursive=False)
        if len(cells) < 2:
            continue
        team_a = cells[0].find("a")
        venue_a = cells[1].find("a")
        if not team_a or not venue_a:
            continue
        team_id = _team_id_from_href(team_a.get("href", ""))
        cn = _venue_cn_from_href(venue_a.get("href", ""))
        if team_id is None or cn is None:
            continue
        team_venue[team_id] = cn
    return team_venue


def team_venue_addresses(bond_id: int, s_code: str) -> dict[int, str]:
    """Koppelt elk team-id aan het volledige adres van zijn speelgelegenheid,
    via /web/teams (team -> cn) en /web/speelgelegenheden (cn -> adres). Geeft
    een lege dict terug (in plaats van te crashen) als een van beide feeds
    niet opgehaald kan worden — locatie is een handig extraatje, geen
    voorwaarde om wedstrijden te kunnen synchroniseren."""
    try:
        teams_html = fetch_teams(bond_id, s_code)
        venues_html = fetch_speelgelegenheden(bond_id, s_code)
    except TeambeheerFetchError:
        return {}

    team_venue = parse_teams(teams_html)
    venues = parse_speelgelegenheden(venues_html)
    return {
        team_id: venues[cn].volledig_adres
        for team_id, cn in team_venue.items()
        if cn in venues and venues[cn].volledig_adres
    }


def _our_fixtures(fixtures: list[TeambeheerFixture], team_id: int) -> list[TeambeheerFixture]:
    return [f for f in fixtures if f.thuis_id == team_id or f.uit_id == team_id]


def _external_id(config: TeambeheerConfig, s_code: str, fixture: TeambeheerFixture) -> str:
    return f"tb-{config.bond_id}-{s_code}-sw{fixture.speelweek}-{fixture.thuis_id}-{fixture.uit_id}"


def preview_team_fixtures(db: Session, config: TeambeheerConfig, season: Season) -> list[dict]:
    """Haalt de poule op en toont onze wedstrijden zonder iets op te slaan."""
    s_code = season_code(season.startjaar)
    html = fetch_jaarprogramma(config.bond_id, s_code, config.poule)
    fixtures = _our_fixtures(parse_jaarprogramma(html), config.team_id)
    venue_addresses = team_venue_addresses(config.bond_id, s_code)

    preview: list[dict] = []
    for fixture in fixtures:
        datum = resolve_year(fixture.datum_raw, season.startjaar, season.eindjaar)
        if datum is None:
            status = "geen_datum"
        else:
            external_id = _external_id(config, s_code, fixture)
            exists = db.query(Match.id).filter(Match.external_id == external_id).first()
            status = "bestaand" if exists else "nieuw"

        preview.append(
            {
                "speelweek": fixture.speelweek,
                "datum": datum,
                "datum_raw": fixture.datum_raw,
                "thuisteam": fixture.thuis_naam.strip(),
                "uitteam": fixture.uit_naam.strip(),
                "locatie": venue_addresses.get(fixture.thuis_id),
                "uitslag": fixture.score.strip() or None,
                "status": status,
            }
        )
    return preview


def sync_team_fixtures(db: Session, config: TeambeheerConfig, season: Season) -> dict:
    """Haalt de poule op en zet nieuwe/gewijzigde wedstrijden in de database.

    Zie functioneel ontwerp v1 sectie 6 (import) en 7 (signaleren van nieuwe/
    gewijzigde wedstrijden via het notificatiecentrum).
    """
    s_code = season_code(season.startjaar)
    html = fetch_jaarprogramma(config.bond_id, s_code, config.poule)
    fixtures = _our_fixtures(parse_jaarprogramma(html), config.team_id)
    venue_addresses = team_venue_addresses(config.bond_id, s_code)

    created = updated = unchanged = skipped_no_date = 0
    resolved_team_naam: str | None = None
    all_players = db.query(Player).all()

    for fixture in fixtures:
        if resolved_team_naam is None:
            if fixture.thuis_id == config.team_id:
                resolved_team_naam = fixture.thuis_naam.strip()
            elif fixture.uit_id == config.team_id:
                resolved_team_naam = fixture.uit_naam.strip()

        datum = resolve_year(fixture.datum_raw, season.startjaar, season.eindjaar)
        if datum is None:
            skipped_no_date += 1
            continue

        thuisteam = fixture.thuis_naam.strip()
        uitteam = fixture.uit_naam.strip()
        locatie = venue_addresses.get(fixture.thuis_id)
        uitslag = fixture.score.strip() or None
        external_id = _external_id(config, s_code, fixture)

        match = db.query(Match).filter(Match.external_id == external_id).first()
        if match:
            schedule_changed = (
                match.datum != datum or match.thuisteam != thuisteam or match.uitteam != uitteam
            )
            uitslag_changed = bool(uitslag) and match.uitslag != uitslag

            if schedule_changed:
                old_datum = match.datum
                match.datum = datum
                match.thuisteam = thuisteam
                match.uitteam = uitteam
                notify_all_players(
                    db,
                    type_="match_changed",
                    title=f"⚠️ Wedstrijd gewijzigd: {thuisteam} - {uitteam}",
                    body=f"Was: {old_datum.strftime('%d-%m-%Y')} — nu: {datum.strftime('%d-%m-%Y')}",
                    match_id=match.id,
                )
            if uitslag_changed:
                match.uitslag = uitslag
                match.status = MatchStatus.GESPEELD

            if schedule_changed or uitslag_changed:
                updated += 1
            else:
                unchanged += 1
            # Alleen aanvullen als er nog geen locatie staat — een handmatige
            # correctie via Beheer > Wedstrijden wordt nooit overschreven.
            if not match.locatie and locatie:
                match.locatie = locatie
            continue

        match = Match(
            external_id=external_id,
            season_id=season.id,
            type=MatchType.COMPETITIE,
            nummer=f"SW{fixture.speelweek}",
            datum=datum,
            thuisteam=thuisteam,
            uitteam=uitteam,
            locatie=locatie,
            uitslag=uitslag,
            status=MatchStatus.GESPEELD if uitslag else MatchStatus.GEPLAND,
        )
        db.add(match)
        db.flush()
        for player in all_players:
            db.add(
                Availability(match_id=match.id, player_id=player.id, status=AvailabilityStatus.NO_RESPONSE)
            )
        notify_all_players(
            db,
            type_="new_match",
            title=f"🆕 Nieuwe wedstrijd: {thuisteam} - {uitteam}",
            body=datum.strftime("%d-%m-%Y"),
            match_id=match.id,
        )
        created += 1

    if resolved_team_naam:
        config.team_naam = resolved_team_naam
    config.last_synced_at = datetime.now(timezone.utc)
    config.last_sync_status = "ok"
    config.last_sync_message = (
        f"{created} nieuw, {updated} gewijzigd, {unchanged} ongewijzigd, "
        f"{skipped_no_date} zonder datum (n.n.b.)"
    )
    db.commit()

    return {
        "created": created,
        "updated": updated,
        "unchanged": unchanged,
        "skipped_no_date": skipped_no_date,
        "team_naam": config.team_naam,
    }
