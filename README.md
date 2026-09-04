# Teamplanning – De Gouv

Webapp die de Excel-planning voor beschikbaarheid en opstelling vervangt door
een centrale database met een spelerscherm, captain-scherm en beheerscherm.
Zie `docs/functioneel-ontwerp-v1.md` voor het volledige functioneel ontwerp.

**Fase 1 MVP** (ontwerp sectie 16):

- Spelers loggen in, zien hun eerstvolgende wedstrijd en geven beschikbaarheid
  door (Ja / Nee / Indien nodig). Dat kan ook vooraf voor latere wedstrijden:
  elke wedstrijd in "Mijn komende wedstrijden" is uitklapbaar met dezelfde
  keuzeknoppen.
- Captains zien de beschikbaarheid per wedstrijd, stellen een opstelling samen
  en publiceren die naar de spelers. "Publiceren" verstuurt niets extern (geen
  e-mail): het zet de opstelling zichtbaar voor spelers in de app en maakt een
  in-app melding. Voor de WhatsApp-groep staat er een aparte knop "📋 Kopieer
  opstelling voor WhatsApp" die een kant-en-klaar tekstberichtje (wedstrijd,
  datum, locatie, geselecteerde spelers) naar het klembord kopieert — inclusief
  een Google Maps-link op de locatieregel, die WhatsApp automatisch als
  aanklikbare navigatielink toont.
- De opstelling is ook achteraf aan te passen — ook voor al gespeelde
  wedstrijden (via **Geschiedenis → Opstelling aanpassen**) en met iedereen
  selecteerbaar, ook wie eerder "kan niet" aangaf, voor een late wissel.
  Statistieken (**Beheer → Statistieken**, "keer opgesteld") tellen live mee,
  dus die blijven altijd kloppen met de laatst opgeslagen opstelling.
- Beschikbaarheid en opstelling staan bij de captain in één compacte tabel:
  per speler de status (kan / kan niet / indien nodig) en een ster (★) om
  die speler in de opstelling te zetten, in plaats van twee aparte lijsten
  onder elkaar.
- **Beheer → Spelers** beheert spelers: aanmaken, naam/rol/e-mailadres/actief
  bewerken, ontgrendelwachtwoord wijzigen en verwijderen. E-mailadres is
  optioneel (alleen nodig als je het echt wilt bijhouden — voor inloggen of
  publiceren is het niet vereist).
- **Beheer → Wedstrijden** laat bestaande wedstrijden bewerken (datum, teams,
  locatie, type, seizoen). Een locatie is meteen een tikbare Google
  Maps-link (op elk scherm waar de locatie getoond wordt) — vul bij voorkeur
  het volledige adres in, dan kun je er direct mee navigeren.

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

**Fase 3** (ontwerp sectie 16):

- **Seizoenen**: **Beheer → Seizoenen** beheert seizoenen en wijst er één als
  actief aan; nieuwe wedstrijden krijgen automatisch het actieve seizoen.
  Wedstrijden, statistieken en de wedstrijdhistorie zijn filterbaar per
  seizoen. Je geeft alleen het startjaar op (bv. `2026`) — het eindjaar is
  altijd startjaar + 1 en wordt automatisch berekend, dat kan niet meer per
  ongeluk fout ingevuld worden.
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

Excel-import en -verschilcontrole zijn uit het ontwerp geschrapt — met de
Teambeheer-sync als bron voor wedstrijden is dat niet meer nodig. De app is
bewust gebouwd voor precies één team (De Gouv) — geen multi-team
ondersteuning met gescheiden spelers/captains/wedstrijden per team.

**Inloggen** (vervangt het oorspronkelijke e-mail/wachtwoord-scherm):

- Eerst een gedeeld **teamwachtwoord** (voorkomt dat buitenstaanders de
  namenlijst kunnen zien), daarna **"Ik ben: [naam]"** — spelers loggen
  meteen in door hun naam te kiezen, geen wachtwoord nodig.
- Captain- en beheeraccounts (🔒 in de lijst) vragen daarbij om hun
  persoonlijke **ontgrendelwachtwoord**, ingesteld per account via
  **Beheer → Spelers**. Het teamwachtwoord zelf is wijzigbaar via
  **Beheer → Instellingen**. Captains en beheerders wijzigen hun eigen
  ontgrendelwachtwoord zelf via het ⚙️-icoon in de navigatie (**Mijn
  account**), zonder tussenkomst van Beheer → Spelers.
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

## Teambeheer synchroniseren

Ga naar **Beheer → Teambeheer**, kies het seizoen en vul in:

- **Bond** (`d=` in de feed-URL, bv. `11` voor SDC)
- **Poule** (`div=`, bv. `1A`)
- **Teamnummer** (`t=` uit de team-URL van je eigen team, bv.
  `https://feeds.teambeheer.nl/web/team?d=11&t=3852&s=26-27` → `3852`)

Voorbeeld voor seizoen 2026-2027, bond 11, poule 1A:
`https://feeds.teambeheer.nl/web/jaarprogramma?d=11&s=26-27&div=1A` — dus
**Bond** `11`, **Poule** `1A`, en het seizoen (`s=26-27`) wordt automatisch
afgeleid van het gekozen seizoen in de app. Voor een volgend seizoen hoef je
dus alleen een nieuw seizoen (bv. startjaar 2027) aan te maken en aan
dezelfde koppeling te hangen — bond en poule blijven meestal gelijk, alleen
`s=` schuift automatisch mee.

De app haalt daarmee `https://feeds.teambeheer.nl/web/jaarprogramma?d=<bond>&s=<seizoen>&div=<poule>`
op — een HTML-pagina, geen API — en parst per speelweek de tabel met datum,
thuisteam, uitteam en (indien al gespeeld) de uitslag. Alleen wedstrijden
waarin het opgegeven teamnummer voorkomt (thuis of uit) worden
geïmporteerd. Het seizoen (`s=`) wordt afgeleid van het gekozen seizoen
(`startjaar`-`eindjaar`, bv. 2026 → `26-27`). Een datum die nog als `n.n.b.`
op de feed staat, wordt overgeslagen tot een latere sync er een echte datum
voor heeft — dat telt mee als "nog zonder datum" in het importresultaat.

Zodra een wedstrijd gespeeld is, staat de uitslag (bv. `7-2`) ook gewoon op
de jaarprogramma-pagina — die wordt bij elke sync meegenomen: de
wedstrijdstatus gaat automatisch naar "Gespeeld" en de uitslag is te zien in
**Geschiedenis** en **Beheer → Wedstrijden** (en daar ook handmatig te
corrigeren, mocht dat nodig zijn). Is de uitslag op de feed een link naar het
officiële wedstrijdformulier, dan is de uitslag in de app ook meteen
doorklikbaar naar die pagina.

Daarbij haalt de app ook `/web/teams` (team → speelgelegenheid) en
`/web/speelgelegenheden` (speelgelegenheid → naam + adres) op om de locatie
van elke wedstrijd automatisch te vullen met naam én adres van de
speelgelegenheid van de thuisspelende ploeg (bv. "Café de Gouverneur,
Munstersestraat 2, Raalte") — meteen bruikbaar als Google Maps-link (zie
hierboven). Dat gebeurt alleen voor wedstrijden die nog geen locatie hebben:
een locatie die je zelf via **Beheer → Wedstrijden** hebt aangepast, wordt
nooit overschreven. Lukt het ophalen van die twee feeds een keer niet, dan
gaat de sync van de wedstrijden gewoon door, alleen zonder locatie erbij.

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
(`backend/alembic/versions/`) voor het schema: `users`, `players`,
`seasons` (met `actief`-vlag), `competitions`, `matches`, `availability`,
`lineups`, `lineup_players`, `audit_log` (wijzigingsgeschiedenis, ontwerp
sectie 10), `notifications` (in-app notificatiecentrum, fase 3) en
`teambeheer_configs` (Teambeheer-koppeling per seizoen).

## Nog niet gebouwd

- Herinneringen en notificaties via e-mail of push (alleen in-app)

## Niet meer in scope

- **Excel importeren en -verschilcontrole** (ontwerp secties 4, 5 en 8) zijn
  geschrapt: met de Teambeheer-sync als bron voor wedstrijden is een
  Excel-import of -vergelijking niet meer relevant.
- **Multi-team ondersteuning**: de app is bewust gebouwd voor precies één
  team (De Gouv), geen meerdere teams met gescheiden spelers/captains/
  wedstrijden.
