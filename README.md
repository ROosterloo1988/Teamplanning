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

**Fase 2** (ontwerp sectie 16, deels — Teambeheer-sync en Excel-verschilcontrole
zijn bewust nog niet gebouwd):

- **Wijzigingslog**: elke wijziging in beschikbaarheid en opstelling wordt
  gelogd (wie, wanneer, oude → nieuwe waarde). Zichtbaar via **Beheer →
  Logboek** en als inklapbare "Geschiedenis" op de captain-wedstrijdpagina.
- **Herinneringen (in-app)**: spelers zien een banner als ze binnen 3 dagen
  voor de wedstrijd nog niet gereageerd hebben; captains zien op hun
  wedstrijdenoverzicht welke wedstrijden nog ontbrekende reacties hebben.
- **Betere statistieken**: **Beheer → Statistieken** toont per speler het
  reactiepercentage en de verdeling kan/kan niet/indien nodig/geen
  antwoord/aantal keer opgesteld.

Fase 3 (meerdere teams/seizoenen, automatische notificaties, PWA) is nog niet
gebouwd. Automatische Teambeheer-sync en Excel-verschilcontrole zijn bewust
uitgesteld (zie hieronder).

## Techniek

- **Backend**: FastAPI + SQLAlchemy + Alembic, PostgreSQL
- **Frontend**: Next.js (App Router) + TypeScript + Tailwind CSS, mobile-first
- **Infra**: Docker Compose (postgres, backend, frontend)

## Snel starten met Docker

```bash
cp .env.example .env
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api (docs op `/docs`)

Bij de eerste start maakt de backend automatisch een beheerder-account aan met
de gegevens uit `.env` (`ADMIN_EMAIL` / `ADMIN_PASSWORD`, standaard
`admin@teamplanning.local` / `changeme`). Log daarmee in en maak via
**Beheer → Spelers** de echte spelersaccounts aan.

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

## Databaseschema

Zie `backend/app/models/` en de eerste Alembic-migratie
(`backend/alembic/versions/0001_initial.py`) voor het schema: `users`,
`players`, `teams`, `seasons`, `competitions`, `matches`, `availability`,
`lineups`, `lineup_players` en `audit_log` (wijzigingsgeschiedenis, ontwerp
sectie 10).

## Nog niet gebouwd

- Automatische nachtelijke synchronisatie met de Teambeheer-feed (fase 2,
  bewust uitgesteld — de feedstructuur is nog niet technisch geïnspecteerd)
- Excel-verschilcontrole ("Excel overnemen" / "App behouden", fase 2, bewust
  uitgesteld)
- Herinneringen via e-mail of push (fase 2 heeft alleen in-app herinneringen)
- Meerdere teams en seizoenen tegelijk, automatische notificaties, PWA (fase 3)
