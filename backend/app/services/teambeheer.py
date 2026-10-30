"""Import van de Teambeheer SDC team-feed.

De feed (https://feeds.teambeheer.nl/web/team?d=<bond>&t=<team>&s=<seizoen>)
is geen data-API maar een Semantic-UI HTML-pagina. Die pagina gebruikt het
responsive "computer only row"/"tablet only row"/"mobile only row"-patroon
meerdere keren (ook voor bv. de menubalk) — de juiste sectie is de
".computer"-div die een "Wedstrijden"-koptekst (h1-h4) bevat, met daarna
één tabel met ALLE wedstrijden van dit ene team (competitie én beker door
elkaar), dus geen filterstap nodig. Elke rij heeft een `title`-attribuut op
de eerste kolom met Teambeheer's eigen, wereldwijd unieke wedstrijd-id
(dezelfde `w=`-waarde als in de link naar /web/wedstrijdformulier/) —
stabieler dan speelweek+teams, want die verschuiven bij een reschedule naar
een andere ronde. Bekerwedstrijden zijn te herkennen aan een rondenummer dat
met "b" begint (bv. "b1", "b2"); een "Vrije week" (bye) heeft geen
tegenstander-link en wordt overgeslagen. Team-namen zijn links naar
/web/team?d=<bond>&t=<teamnummer>&s=<seizoen>.
Zie functioneel ontwerp v1 secties 6 en 7.
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
from app.services.availability import reset_availability
from app.services.notifications import notify_all_players

TEAM_DATUM_RE = re.compile(r"^(\d{2})-(\d{2})-(\d{4})$")


class TeambeheerFetchError(Exception):
    """De team-pagina kon niet opgehaald of gelezen worden."""


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
    # Zodra een wedstrijd officieel is afgehandeld, is de score-cel een link
    # naar het wedstrijdformulier (/web/wedstrijdformulier/?d=&w=&s=) — een
    # handmatig ingevulde score zonder formulier is gewoon platte tekst.
    score_url: str | None = None


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

    @property
    def label(self) -> str:
        """Naam + adres, bv. 'Café de Gouverneur, Munstersestraat 2, Raalte' —
        zo weet je meteen welke zaak het is, niet alleen het kale adres."""
        parts = [p.strip() for p in (self.naam, self.volledig_adres) if p and p.strip()]
        return ", ".join(parts)


def season_code(startjaar: int) -> str:
    """2026 -> '26-27', zoals gebruikt in de s=-queryparameter."""
    return f"{startjaar % 100:02d}-{(startjaar + 1) % 100:02d}"


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


def fetch_team_page(bond_id: int, s_code: str, team_id: int) -> str:
    return _fetch_page("/web/team", {"d": bond_id, "s": s_code, "t": team_id})


def fetch_speelgelegenheden(bond_id: int, s_code: str) -> str:
    return _fetch_page("/web/speelgelegenheden", {"d": bond_id, "s": s_code})


def fetch_teams(bond_id: int, s_code: str) -> str:
    return _fetch_page("/web/teams", {"d": bond_id, "s": s_code})


def parse_team_page(html: str) -> list[TeamFixture]:
    """/web/team?d=<bond>&t=<team>&s=<seizoen> — het volledige programma van
    dit ene team (competitie én beker door elkaar), dus geen filterstap
    nodig. De pagina gebruikt het responsive "computer only row"-patroon
    meerdere keren (ook voor bv. de menubalk) — we doorzoeken daarom ALLE
    ".computer"-secties tot de juiste (met een "Wedstrijden"-koptekst)
    gevonden is, in plaats van blind de eerste te pakken. Leest bewust geen
    tablet/mobiel-secties: die tonen dezelfde wedstrijden nog eens met
    afgekapte datums en zonder stabiele id, en zouden alles dus laten
    dubbeltellen."""
    soup = BeautifulSoup(html, "html.parser")

    table = None
    for section in soup.find_all("div", class_="computer"):
        # Niet via `string=`: dat vereist dat de tag precies één platte-
        # tekst-kind heeft, en faalt stilletjes zodra er bv. een icoontje
        # naast de koptekst staat (<h2><i class="..."></i>Wedstrijden</h2>)
        # — dan is `.string` None ook al toont de kop gewoon "Wedstrijden".
        # get_text() werkt wel door zulke geneste tags heen.
        header = next(
            (h for h in section.find_all(["h1", "h2", "h3", "h4"]) if "Wedstrijden" in h.get_text()),
            None,
        )
        if header:
            table = header.find_next("table")
            break
    if not table:
        return []

    tbody = table.find("tbody")
    if not tbody:
        return []

    fixtures: list[TeamFixture] = []
    for row in tbody.find_all("tr", recursive=False):
        cells = row.find_all("td", recursive=False)
        if len(cells) < 4:
            continue

        official_id_raw = cells[0].get("title")
        if not official_id_raw:
            continue
        try:
            official_id = int(official_id_raw)
        except ValueError:
            continue
        ronde = cells[0].get_text(strip=True)

        datum_raw = cells[1].get_text(strip=True)
        thuis_a = cells[2].find("a")
        uit_a = cells[3].find("a")
        if not thuis_a or not uit_a:
            # Een "Vrije week" (bye) in de bekerpoule: geen echte wedstrijd.
            continue
        thuis_id = _team_id_from_href(thuis_a.get("href", ""))
        uit_id = _team_id_from_href(uit_a.get("href", ""))
        if thuis_id is None or uit_id is None:
            continue

        score_cell = cells[4] if len(cells) > 4 else None
        score_a = score_cell.find("a") if score_cell else None
        if score_a:
            score = score_a.get_text(strip=True)
            score_url = (
                f"{settings.TEAMBEHEER_BASE_URL}{score_a['href']}" if score_a.get("href") else None
            )
        else:
            # Een niet-bevestigde of handmatig ingevulde score zonder
            # wedstrijdformulier is gewoon platte tekst (geen win/verlies-badge).
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


def team_venues(bond_id: int, s_code: str) -> dict[int, Venue]:
    """Koppelt elk team-id aan zijn Venue (naam + adres van de
    speelgelegenheid), via /web/teams (team -> cn) en
    /web/speelgelegenheden (cn -> Venue). Geeft een lege dict terug (in
    plaats van te crashen) als een van beide feeds niet opgehaald kan
    worden — locatie is een handig extraatje, geen voorwaarde om
    wedstrijden te kunnen synchroniseren."""
    try:
        teams_html = fetch_teams(bond_id, s_code)
        venues_html = fetch_speelgelegenheden(bond_id, s_code)
    except TeambeheerFetchError:
        return {}

    team_venue = parse_teams(teams_html)
    venues = parse_speelgelegenheden(venues_html)
    return {team_id: venues[cn] for team_id, cn in team_venue.items() if cn in venues}


def team_venue_addresses(bond_id: int, s_code: str) -> dict[int, str]:
    """Zoals team_venues, maar geeft meteen het label (naam + adres) terug,
    bv. 'Café de Gouverneur, Munstersestraat 2, Raalte'."""
    return {team_id: venue.label for team_id, venue in team_venues(bond_id, s_code).items() if venue.label}


def _external_id(official_id: int) -> str:
    """De 'w='-waarde uit /web/wedstrijdformulier is Teambeheer's eigen,
    wereldwijd unieke wedstrijd-id."""
    return f"tb-m{official_id}"


def _lookup_match(db: Session, season_id: int, external_id: str, thuisteam: str, uitteam: str) -> Match | None:
    """Zoekt eerst op de (nieuwe) team-feed-id, en anders als fallback op
    season + team-namen — dat vangt wedstrijden die nog met het oude
    jaarprogramma-schema zijn geïmporteerd en voorkomt dat ze hier als
    dubbele wedstrijd worden aangemaakt."""
    match = db.query(Match).filter(Match.external_id == external_id).first()
    if match:
        return match
    return (
        db.query(Match)
        .filter(
            Match.season_id == season_id,
            Match.thuisteam == thuisteam,
            Match.uitteam == uitteam,
            Match.external_id != external_id,
        )
        .first()
    )


def preview_team_fixtures(db: Session, config: TeambeheerConfig, season: Season) -> list[dict]:
    """Haalt het volledige programma van dit team op en toont het zonder
    iets op te slaan."""
    s_code = season_code(season.startjaar)
    html = fetch_team_page(config.bond_id, s_code, config.team_id)
    fixtures = parse_team_page(html)
    venue_addresses = team_venue_addresses(config.bond_id, s_code)

    preview: list[dict] = []
    for fixture in fixtures:
        datum = resolve_team_date(fixture.datum_raw)
        thuisteam = fixture.thuis_naam.strip()
        uitteam = fixture.uit_naam.strip()
        if datum is None:
            status = "geen_datum"
        else:
            external_id = _external_id(fixture.official_id)
            exists = _lookup_match(db, season.id, external_id, thuisteam, uitteam)
            status = "bestaand" if exists else "nieuw"

        preview.append(
            {
                "ronde": fixture.ronde,
                "is_beker": fixture.is_beker,
                "datum": datum,
                "datum_raw": fixture.datum_raw,
                "thuisteam": thuisteam,
                "uitteam": uitteam,
                "locatie": venue_addresses.get(fixture.thuis_id),
                "uitslag": fixture.score.strip() or None,
                "uitslag_url": fixture.score_url,
                "status": status,
            }
        )
    return preview


def sync_team_fixtures(db: Session, config: TeambeheerConfig, season: Season) -> dict:
    """Haalt het volledige programma van dit team op (competitie én beker)
    en zet nieuwe/gewijzigde wedstrijden in de database.

    Zie functioneel ontwerp v1 sectie 6 (import) en 7 (signaleren van nieuwe/
    gewijzigde wedstrijden via het notificatiecentrum).
    """
    s_code = season_code(season.startjaar)
    html = fetch_team_page(config.bond_id, s_code, config.team_id)
    fixtures = parse_team_page(html)
    venues = team_venues(config.bond_id, s_code)

    created = updated = unchanged = skipped_no_date = 0
    resolved_team_naam: str | None = None
    all_players = db.query(Player).all()

    for fixture in fixtures:
        if resolved_team_naam is None:
            if fixture.thuis_id == config.team_id:
                resolved_team_naam = fixture.thuis_naam.strip()
            elif fixture.uit_id == config.team_id:
                resolved_team_naam = fixture.uit_naam.strip()

        datum = resolve_team_date(fixture.datum_raw)
        thuisteam = fixture.thuis_naam.strip()
        uitteam = fixture.uit_naam.strip()
        external_id = _external_id(fixture.official_id)

        if datum is None:
            # Was deze wedstrijd eerder wel gepland en staat hij nu weer
            # zonder (bekende) datum (uitgesteld, nieuwe datum nog
            # onbekend)? Dan laten we de laatst bekende datum staan (die
            # kolom is not-null) maar zetten 'm zichtbaar op "onbekend" en
            # laten spelers dat weten — anders blijft de oude datum overal
            # stilletjes als geldig ogen.
            existing = _lookup_match(db, season.id, external_id, thuisteam, uitteam)
            if existing and existing.external_id != external_id:
                existing.external_id = external_id
            if existing and not existing.datum_onbekend:
                existing.datum_onbekend = True
                # Eerder gegeven "ja"/"nee" sloeg op de (nu vervallen) datum
                # en zegt niets over wanneer de wedstrijd straks wél is.
                reset_availability(db, existing.id)
                notify_all_players(
                    db,
                    type_="match_changed",
                    title=f"⚠️ Datum nog niet bekend: {thuisteam} - {uitteam}",
                    body=(
                        f"Was: {existing.datum.strftime('%d-%m-%Y')} — wedstrijd is uitgesteld, "
                        "nieuwe datum nog niet bekend. Geef je beschikbaarheid opnieuw door zodra "
                        "de nieuwe datum bekend is."
                    ),
                    match_id=existing.id,
                )
                updated += 1
            elif not existing:
                skipped_no_date += 1
            else:
                unchanged += 1
            continue

        venue = venues.get(fixture.thuis_id)
        locatie = venue.label if venue and venue.label else None
        uitslag = fixture.score.strip() or None
        uitslag_url = fixture.score_url

        match = _lookup_match(db, season.id, external_id, thuisteam, uitteam)
        if match:
            if match.external_id != external_id:
                # Was nog geïmporteerd via het oude jaarprogramma-schema —
                # hernoem naar de nieuwe, stabiele team-feed-id in plaats van
                # 'm als dubbele wedstrijd aan te maken.
                match.external_id = external_id
            date_changed = match.datum != datum or match.datum_onbekend
            schedule_changed = (
                date_changed or match.thuisteam != thuisteam or match.uitteam != uitteam
            )
            uitslag_changed = bool(uitslag) and (
                match.uitslag != uitslag or match.uitslag_url != uitslag_url
            )

            if schedule_changed:
                old_datum = match.datum
                old_datum_onbekend = match.datum_onbekend
                match.datum = datum
                match.datum_onbekend = False
                match.thuisteam = thuisteam
                match.uitteam = uitteam
                if date_changed:
                    # Een echte datumwijziging maakt eerder gegeven
                    # beschikbaarheid onbetrouwbaar — die sloeg op de oude
                    # datum, niet op de nieuwe.
                    reset_availability(db, match.id)
                notify_all_players(
                    db,
                    type_="match_changed",
                    title=f"⚠️ Wedstrijd gewijzigd: {thuisteam} - {uitteam}",
                    body=(
                        f"Was: {'datum nog niet bekend' if old_datum_onbekend else old_datum.strftime('%d-%m-%Y')}"
                        f" — nu: {datum.strftime('%d-%m-%Y')}"
                        + (" Geef je beschikbaarheid opnieuw door." if date_changed else "")
                    ),
                    match_id=match.id,
                )
            if uitslag_changed:
                match.uitslag = uitslag
                match.uitslag_url = uitslag_url
                match.status = MatchStatus.GESPEELD

            if schedule_changed or uitslag_changed:
                updated += 1
            else:
                unchanged += 1
            # Alleen aanvullen als er nog geen locatie staat — een handmatige
            # correctie via Beheer > Wedstrijden wordt nooit overschreven. De
            # ene uitzondering: staat de locatie er nog exact zoals een
            # oudere versie van deze sync 'm zelf zonder cafénaam invulde
            # (alleen straat + plaats), dan is dat geen handmatige edit en
            # mag 'm alsnog geüpgraded worden zodra de naam bekend is.
            if not match.locatie and locatie:
                match.locatie = locatie
            elif (
                match.locatie
                and venue
                and venue.label
                and match.locatie == venue.volledig_adres
                and venue.label != venue.volledig_adres
            ):
                match.locatie = venue.label
            continue

        match = Match(
            external_id=external_id,
            season_id=season.id,
            type=MatchType.BEKER if fixture.is_beker else MatchType.COMPETITIE,
            nummer=fixture.ronde,
            datum=datum,
            thuisteam=thuisteam,
            uitteam=uitteam,
            locatie=locatie,
            uitslag=uitslag,
            uitslag_url=uitslag_url,
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
