"""DartConnect: live/recap-link per wedstrijd.

DartConnect (https://tv.dartconnect.com) scoort sommige wedstrijden live —
niet per se alle poules, en alleen als iemand bij de wedstrijd de
live-scoring daadwerkelijk aanzet: de meeste wedstrijden staan er dus
helemaal niet op, dat is geen bug maar hoe DartConnect werkt.

Een wedstrijd die NU live loopt, heeft zijn eigen live-kijkpagina
(https://tv.dartconnect.com/live/<spectator_key>/<type>/<league>/<season_id>)
— dat is wat je als speler wil tijdens de wedstrijd. Zodra de wedstrijd is
afgelopen, bestaat die pagina niet meer (de spectator_key hoort bij de
live-sessie), en gebruiken we in plaats daarvan de permanente recap-link
(https://recap.dartconnect.com/matches/<dc_match_id>). Vandaar dat we hier
altijd zowel de lopende/live wedstrijden (/matches/live, geeft de
spectator_key) als de afgeronde (/matches, geeft alleen dc_match_id)
ophalen.

Authenticatie is een publieke, accountloze CSRF-cookie-dans (Laravel
Sanctum): eerst GET /sanctum/csrf-cookie, dan het XSRF-TOKEN-cookie als
header meesturen bij de API-call. Geen gebruikersnaam/wachtwoord nodig —
dit is dezelfde aanroep die de publieke tv.dartconnect.com-pagina zelf ook
doet.
"""

from __future__ import annotations

import urllib.parse
from dataclasses import dataclass
from datetime import date, datetime, timezone

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.match import Match
from app.models.season import Season
from app.models.teambeheer import TeambeheerConfig

_USER_AGENT = "Mozilla/5.0 (compatible; TeamplanningSync/1.0)"


class DartConnectFetchError(Exception):
    """De DartConnect-liga-data kon niet opgehaald of gelezen worden."""


@dataclass
class DartConnectMatch:
    league_match_id: int
    dc_match_id: str | None
    sched_date: date | None
    home_name: str
    away_name: str
    completed: bool
    # Alleen gezet voor een wedstrijd die NU live gescoord wordt (komt uit
    # /matches/live) — de echte live-kijklink, hoort bij de live-sessie en
    # is dus niet geldig meer zodra de wedstrijd afgelopen is.
    live_url: str | None = None


def _parse_date(raw: str | None) -> date | None:
    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError:
        return None


def _csrf_headers(client: httpx.Client) -> dict[str, str]:
    base_headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "User-Agent": _USER_AGENT,
        "Referer": f"{settings.DARTCONNECT_TV_BASE_URL}/",
        "X-Requested-With": "XMLHttpRequest",
    }
    # Af en toe zet DartConnect het XSRF-cookie niet mee terug op de eerste
    # poging — simpelweg nog een keer proberen is genoeg.
    last_exc: httpx.HTTPError | None = None
    for _ in range(2):
        try:
            client.get(
                f"{settings.DARTCONNECT_TV_BASE_URL}/sanctum/csrf-cookie",
                headers=base_headers,
                timeout=10,
            )
        except httpx.HTTPError as exc:
            last_exc = exc
            continue
        xsrf = client.cookies.get("XSRF-TOKEN")
        if xsrf:
            headers = dict(base_headers)
            headers["X-XSRF-TOKEN"] = urllib.parse.unquote(xsrf)
            return headers

    if last_exc:
        raise DartConnectFetchError(f"Kon DartConnect niet bereiken: {last_exc}") from last_exc
    raise DartConnectFetchError("Geen CSRF-token ontvangen van DartConnect")


def fetch_league_matches(league: str) -> list[DartConnectMatch]:
    """Haalt alle wedstrijden op (reguliere competitie + bekerrondes: lopend,
    live en afgerond) voor deze DartConnect-liga-slug, bv. "DeSDCC". Niet
    elke wedstrijd staat hierin — alleen wat DartConnect daadwerkelijk live
    gescoord heeft of nog gaat scoren.

    Combineert bewust twee endpoints: een wedstrijd die op dit moment live
    gescoord wordt, staat nog niet in de reguliere /matches-lijst (die toont
    alleen al afgeronde rondes) — die moet apart via /matches/live worden
    opgehaald, anders mist een koppeling precies tijdens de wedstrijd zelf.
    """
    with httpx.Client(follow_redirects=True) as client:
        headers = _csrf_headers(client)
        try:
            response = client.post(
                f"{settings.DARTCONNECT_TV_BASE_URL}/api/league/{league}/matches",
                json={},
                headers=headers,
                timeout=20,
            )
            response.raise_for_status()
            data = response.json()

            live_response = client.post(
                f"{settings.DARTCONNECT_TV_BASE_URL}/api/league/{league}/matches/live",
                json={},
                headers=headers,
                timeout=20,
            )
            live_response.raise_for_status()
            live_data = live_response.json()
        except httpx.HTTPError as exc:
            raise DartConnectFetchError(f"Kon DartConnect-liga niet ophalen: {exc}") from exc

    matches: list[DartConnectMatch] = []
    for section_key in ("reg", "post_completed", "post_break"):
        section = data.get(section_key) or {}
        for by_date in section.values():
            for entries in by_date.values():
                for entry in entries:
                    dc = _match_from_entry(entry)
                    if dc:
                        matches.append(dc)

    for live_entry in live_data.get("matches") or []:
        dc = _match_from_entry(live_entry.get("league_match") or {})
        if not dc:
            continue
        spectator_key = live_entry.get("spectator_key")
        match_type = live_entry.get("match_type")
        event_id = live_entry.get("event_id")
        season_id = live_entry.get("season_id")
        if spectator_key and match_type and event_id and season_id:
            dc.live_url = (
                f"{settings.DARTCONNECT_TV_BASE_URL}/live/{spectator_key}/{match_type}/"
                f"{event_id}/{season_id}"
            )
        matches.append(dc)

    return matches


def _match_from_entry(entry: dict) -> DartConnectMatch | None:
    if not entry or entry.get("is_bye"):
        return None
    left = entry.get("left") or {}
    right = entry.get("right") or {}
    if "id" not in entry:
        return None
    return DartConnectMatch(
        league_match_id=entry["id"],
        dc_match_id=entry.get("dc_match_id"),
        sched_date=_parse_date(entry.get("sched_date")),
        home_name=(left.get("team_name") or "").strip(),
        away_name=(right.get("team_name") or "").strip(),
        # "C" = Completed. Alles anders (bv. "A" = Active) betekent: nog
        # bezig of nog niet begonnen — zolang DartConnect 'm al wel kent
        # (dc_match_id gezet) is dat dus "live".
        completed=entry.get("status") == "C",
    )


def recap_url(dc_match_id: str) -> str:
    return f"{settings.DARTCONNECT_RECAP_BASE_URL}/matches/{dc_match_id}"


# Teambeheer en DartConnect registreren de datum van dezelfde wedstrijd niet
# altijd exact hetzelfde (in de praktijk tot een dag verschil, bv. bij een
# bekerronde) — op exacte datumgelijkheid matchen liet zulke wedstrijden dan
# stilletjes ongekoppeld. In plaats daarvan: op teamnamen matchen en, als er
# meerdere datums voor hetzelfde teampaar in de buurt liggen, de dichtstbije
# nemen — twee teams spelen elkaar normaal niet twee keer binnen een paar
# dagen, dus dit blijft ondubbelzinnig.
MAX_DATE_DIFF_DAYS = 3


def _find_match(
    dc_matches: list[DartConnectMatch], datum: date, thuisteam: str, uitteam: str
) -> DartConnectMatch | None:
    thuisteam_l, uitteam_l = thuisteam.strip().lower(), uitteam.strip().lower()
    best: DartConnectMatch | None = None
    best_diff: int | None = None
    for dc in dc_matches:
        if not dc.dc_match_id or dc.sched_date is None:
            continue
        home_l, away_l = dc.home_name.lower(), dc.away_name.lower()
        # Thuis/uit kan in andere volgorde staan dan bij ons (bv. een
        # verzette wedstrijd op de oorspronkelijke thuislocatie) — op
        # teamnamen matchen, niet op thuis/uit-positie.
        if not (
            (home_l == thuisteam_l and away_l == uitteam_l)
            or (home_l == uitteam_l and away_l == thuisteam_l)
        ):
            continue
        diff = abs((dc.sched_date - datum).days)
        if diff > MAX_DATE_DIFF_DAYS:
            continue
        if best_diff is None or diff < best_diff:
            best, best_diff = dc, diff
    return best


def sync_dartconnect_links(db: Session, config: TeambeheerConfig, season: Season) -> dict:
    """Doorzoekt de DartConnect-liga op wedstrijden die overeenkomen (op
    datum + teamnamen) met onze eigen wedstrijden in dit seizoen, en vult
    `dartconnect_url` in waar die nog ontbreekt of veranderd is (bv. een
    wedstrijd die net live gescoord begon te worden)."""
    dc_matches = fetch_league_matches(config.dartconnect_league)

    matches = db.query(Match).filter(Match.season_id == season.id).all()
    checked = updated = 0
    for match in matches:
        checked += 1
        found = _find_match(dc_matches, match.datum, match.thuisteam, match.uitteam)
        if found and found.dc_match_id:
            new_url = found.live_url if (not found.completed and found.live_url) else recap_url(
                found.dc_match_id
            )
            if match.dartconnect_url != new_url or match.dartconnect_completed != found.completed:
                match.dartconnect_url = new_url
                match.dartconnect_completed = found.completed
                updated += 1

    matched = sum(1 for m in matches if m.dartconnect_url)
    config.last_dartconnect_sync_at = datetime.now(timezone.utc)
    config.last_dartconnect_sync_status = "ok"
    config.last_dartconnect_sync_message = f"{matched} van {checked} wedstrijden gekoppeld aan DartConnect"
    db.commit()

    return {"checked": checked, "matched": matched, "updated": updated}
