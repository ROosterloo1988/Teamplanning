# Teamplanning – De Gouv

Webapp die de Excel-planning voor beschikbaarheid en opstelling vervangt door
een centrale database met een spelerscherm, captain-scherm en beheerscherm.
Zie `docs/functioneel-ontwerp-v1.md` voor het volledige functioneel ontwerp.

**Fase 1 MVP** (ontwerp sectie 16):

- Spelers loggen in, zien hun eerstvolgende wedstrijd en geven beschikbaarheid
  door (Ja / Nee / Indien nodig).
- Captains zien de beschikbaarheid per wedstrijd, stellen een opstelling samen
  en publiceren die naar de spelers.
- Beheer beheert spelers en wedstrijden, en importeert de bestaande Excel-planning.

**Fase 2** (ontwerp sectie 16):

- **Wijzigingslog**: elke wijziging in beschikbaarheid en opstelling wordt
  gelogd (wie, wanneer, oude → nieuwe waarde). Zichtbaar via **Beheer →
  Logboek** en als inklapbare "Geschiedenis" op de captain-wedstrijdpagina.
- **Herinneringen (in-app)**: spelers zien een banner als ze binnen 3 dagen
  voor de wedstrijd nog niet gereageerd hebben; captains zien op hun
  wedstrijdenoverzicht welke wedstrijden nog ontbrekende reacties hebben.
- **Betere statistieken**: **Beheer → Statistieken** toont per speler het
  reactiepercentage en de verdeling kan/kan niet/indien nodig/geen
  antwoord/aantal keer opgesteld.

**Fase 3** (ontwerp sectie 16, deels — volledige multi-team ondersteuning is
een leuke uitbreiding voor later, maar nu niet nodig, zie hieronder):

- **Seizoenen**: **Beheer → Seizoenen** beheert seizoenen en wijst er één als
  actief aan; nieuwe wedstrijden krijgen automatisch het actieve seizoen.
  Wedstrijden, statistieken en de wedstrijdhistorie zijn filterbaar per
  seizoen.
- **Wedstrijdhistorie**: **Geschiedenis** (voor alle rollen) toont afgelopen
  wedstrijden met de gepubliceerde opstelling, filterbaar per seizoen.
- **In-app notificatiecentrum**: een bel-icoon met ongelezen-badge in de
  navigatie en een **Meldingen**-pagina. Spelers met een account krijgen een
  melding bij een nieuwe wedstrijd en bij een gepubliceerde opstelling.
- **PWA**: de app heeft een manifest en iconen zodat spelers hem op hun
  telefoon kunnen "installeren" (add to home screen).

**Teambeheer-synchronisatie** (ontwerp secties 6 en 7):

- **Beheer → Teambeheer** koppelt een seizoen aan de Teambeheer SDC
  jaarprogramma-feed (bond, poule, teamnummer), met een "Wedstrijden
  ophalen"-preview (nieuw/bestaand/nog geen datum) en een
  "Wedstrijden importeren"-knop.
- Een ingebouwde nachtelijke achtergrondtaak doet dit automatisch voor elk
  gekoppeld seizoen en meldt nieuwe of gewijzigde wedstrijden via het
  notificatiecentrum — uit te zetten met `TEAMBEHEER_AUTO_SYNC=false`.

Excel-verschilcontrole (fase 2) is uit het ontwerp geschrapt — met de
Teambeheer-sync als bron is dat niet meer nodig. Volledige multi-team
ondersteuning (meerdere teams met gescheiden spelers/captains/wedstrijden en
een team-wisselaar) is een leuke uitbreiding voor later, maar niet nodig op
dit moment — de app werkt voorlopig voor één team, nu met seizoenen
erbovenop.

**Inloggen** (vervangt het oorspronkelijke e-mail/wachtwoord-scherm):

- Eerst een gedeeld **teamwachtwoord** (voorkomt dat buitenstaanders de
  namenlijst kunnen zien), daarna **"Ik ben: [naam]"** — spelers loggen
  meteen in door hun naam te kiezen, geen wachtwoord nodig.
- Captain- en beheeraccounts (🔒 in de lijst) vragen daarbij om hun
  persoonlijke **ontgrendelwachtwoord**, ingesteld per account via
  **Beheer → Spelers**. Het teamwachtwoord zelf is wijzigbaar via
  **Beheer → Instellingen**.
- Het teamwachtwoord blijft op het toestel onthouden (90 dagen); uitloggen
  brengt je terug naar de naam-kiezer, niet naar het teamwachtwoord-scherm.

## Techniek

- **Backend**: FastAPI + SQLAlchemy + Alembic, PostgreSQL
- **Frontend**: Next.js (App Router) + TypeScript + Tailwind CSS, mobile-first
- **Infra**: Docker Compose (postgres, backend, frontend). De frontend
  proxyt `/api` server-side naar de backend (`frontend/next.config.mjs`), dus
  naar buiten toe is er maar één poort (3000) — handig als SSL-terminatie/
  reverse-proxy op een aparte server staat. Zie
  `docs/deployment-ubuntu-26.04.md` voor een complete installatiehandleiding
  (Ubuntu Server 26.04 LTS, minimized install).

## Snel starten met Docker

```bash
cp .env.example .env
docker compose up --build
```

- App (frontend + de doorgeproxyde API): http://localhost:3000
- Backend rechtstreeks (alleen als je poort 8000 zelf publiceert, bv. voor
  lokaal ontwikkelen buiten Docker): http://localhost:8000/api (docs op
  `/docs`)

Bij de eerste start maakt de backend automatisch een beheerder-account aan
(`ADMIN_EMAIL` / `ADMIN_PASSWORD`, standaard `admin@teamplanning.nl` /
`changeme` — dat wachtwoord is meteen ook het ontgrendelwachtwoord voor de
naam-kiezer) en een teamwachtwoord (`TEAM_ACCESS_PASSWORD`, standaard
`degouv`). Log in met het teamwachtwoord, kies "Beheerder" en ontgrendel met
`ADMIN_PASSWORD`, en maak via **Beheer → Spelers** de echte accounts aan.

## Lokaal ontwikkelen zonder Docker

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

export DATABASE_URL=postgresql+psycopg2://teamplanning:teamplanning@localhost:5432/teamplanning
alembic upgrade head
python -m app.initial_data

uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

## Excel importeren

Ga naar **Beheer → Excel importeren** en upload het huidige planningsbestand
(bijv. `Schema seizoen 26-27-3.xlsx`). Verwacht wordt een werkblad met een
headerrij: `wedstrijdnummer`, `datum`, `thuisteam`, `uitteam`, `locatie`,
gevolgd door één kolom per speler. Celwaarden worden als volgt omgezet
(hoofdletter-ongevoelig, zie ontwerp sectie 4):

| Excel | App |
| ----- | --- |
| `v` / `V` | Kan (AVAILABLE) |
| `x` / `X` | Kan niet (UNAVAILABLE) |
| `?` | Indien nodig (IF_NEEDED) |
| `1` | Kan / opgesteld (AVAILABLE) |
| leeg | Geen antwoord (NO_RESPONSE) |

Een wedstrijdnummer dat begint met `B` wordt als **Beker** geïmporteerd, met
`I` als **Inhaal**, en anders als **Competitie** (ontwerp sectie 5).

## Teambeheer synchroniseren

Ga naar **Beheer → Teambeheer**, kies het seizoen en vul in:

- **Bond** (`d=` in de feed-URL, bv. `11` voor SDC)
- **Poule** (`div=`, bv. `1A`)
- **Teamnummer** (`t=` uit de team-URL van je eigen team, bv.
  `https://feeds.teambeheer.nl/web/team?d=11&t=3852&s=26-27` → `3852`)

De app haalt daarmee `https://feeds.teambeheer.nl/web/jaarprogramma?d=<bond>&s=<seizoen>&div=<poule>`
op — een HTML-pagina, geen API — en parst per speelweek de tabel met datum,
thuisteam en uitteam. Alleen wedstrijden waarin het opgegeven teamnummer
voorkomt (thuis of uit) worden geïmporteerd. Het seizoen (`s=`) wordt
afgeleid van het gekozen seizoen (`startjaar`-`eindjaar`, bv. 2026 → `26-27`).
Een datum die nog als `n.n.b.` op de feed staat, wordt overgeslagen tot een
latere sync er een echte datum voor heeft — dat telt mee als "nog zonder
datum" in het importresultaat.

`Beheer → Teambeheer` laat je eerst preview'en (nieuw/bestaand/nog geen
datum) voordat je importeert. Daarnaast draait er een ingebouwde nachtelijke
achtergrondtaak (standaard 03:30 UTC, `TEAMBEHEER_SYNC_HOUR` /
`TEAMBEHEER_SYNC_MINUTE`) die dit automatisch doet voor elk seizoen met een
koppeling, en spelers een melding stuurt bij een nieuwe of gewijzigde
wedstrijd. Zet `TEAMBEHEER_AUTO_SYNC=false` om dat uit te schakelen.

De parser is los van een live verbinding getest tegen een echte, opgeslagen
Teambeheer-pagina (`backend/tests/fixtures/`) — zie `backend/tests/`
(`pip install -r requirements-dev.txt && pytest`).

## Databaseschema

Zie `backend/app/models/` en de Alembic-migraties
(`backend/alembic/versions/`) voor het schema: `users`, `players`, `teams`,
`seasons` (met `actief`-vlag), `competitions`, `matches`, `availability`,
`lineups`, `lineup_players`, `audit_log` (wijzigingsgeschiedenis, ontwerp
sectie 10), `notifications` (in-app notificatiecentrum, fase 3) en
`teambeheer_configs` (Teambeheer-koppeling per seizoen).

## Nog niet gebouwd

- Herinneringen en notificaties via e-mail of push (alleen in-app)
- Volledige multi-team ondersteuning: meerdere teams met gescheiden
  spelers/captains/wedstrijden en een team-wisselaar door de hele app (leuke
  uitbreiding voor later, nu bewust niet nodig)

## Niet meer in scope

- **Excel-verschilcontrole** ("Excel overnemen" / "App behouden", ontwerp
  sectie 8) is geschrapt: nooit gebouwd, en met de Teambeheer-sync als bron
  voor wedstrijden is een aparte Excel-vergelijking niet meer relevant.
