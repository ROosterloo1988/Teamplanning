# Functioneel ontwerp v1 – Teamplanning De Gouv

## 1. De basis van de applicatie

De belangrijkste verandering:

> **De webapp wordt de database. Excel was ooit de bron, Teambeheer SDC is
> dat nu.**

De gegevens worden dus niet meer "in Excel" bijgehouden. Excel diende alleen
nog als eenmalige migratiebron bij de start (sectie 15); een doorlopende
Excel-verschilcontrole is geschrapt (sectie 8).

```text
                         ┌─────────────────┐
                         │ Teambeheer SDC   │
                         │ wedstrijden/feed │
                         └────────┬────────┘
                                  │
                             automatische
                               import
                                  │
                                  ▼
┌──────────────┐          ┌──────────────────┐
│   Spelers    │─────────▶│  WEBAPP DATABASE │
└──────────────┘          │   PostgreSQL     │
                          └────────┬─────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    ▼              ▼              ▼
                 Speler         Captain        Beheer
                 scherm         scherm         scherm
                    │              │
                    │              ▼
                    │          Opstelling
                    │
                    ▼
              Beschikbaarheid
```

## 2. Spelerscherm

Belangrijkste scherm voor de spelers. Toont welkomstbericht, eerstvolgende
wedstrijd, drie knoppen (Ja / Nee / Indien nodig) en een lijst met komende
wedstrijden inclusief status. De speler hoeft niet meer te weten wat `V`,
`X`, `?` of `1` betekent — na het klikken wordt de keuze direct opgeslagen.

## 3. Captain-scherm

De captain krijgt alle beschikbaarheid per wedstrijd op een rij, kan een
opstelling samenstellen (checkboxes) en publiceren. Na publiceren zien
spelers de opstelling in de app.

## 4. Excel-conversie

Bestaande kolommen (wedstrijdnummer, datum, thuisteam, uitteam, locatie,
spelerskolommen, aantal beschikbare spelers, bekerweken zoals `B1`/`B2`/`B3`)
worden één-op-één geïmporteerd. Celwaarden worden genormaliseerd
(hoofdletter-ongevoelig):

| Excel     | App             |
| --------- | --------------- |
| `v` / `V` | 🟢 Kan          |
| `x` / `X` | 🔴 Kan niet     |
| `?`       | 🟡 Indien nodig |
| `1`       | 🏓 Opgesteld    |
| leeg      | ⚪ Geen antwoord |

## 5. Wedstrijdsoorten

Elke wedstrijd krijgt een type: `COMPETITIE`, `BEKER`, `INHAAL`, `OVERIG`.
`B1` wordt bijvoorbeeld "Beker — ronde/week 1" in plaats van speciale tekst
in een Excel-cel.

## 6. Teambeheer-import

Beheer krijgt een scherm om wedstrijden op te halen uit Teambeheer SDC
(seizoen/afdeling/competitie/poule/team) en nieuwe wedstrijden te importeren.

## 7. Automatische synchronisatie

De app controleert periodiek Teambeheer en meldt nieuwe of gewijzigde
wedstrijden.

## 8. Excel-controle — *geschrapt*

~~Extra beveiliging: de app vergelijkt periodiek app-data met de Excel-bron
en toont verschillen, met de keuze "Excel overnemen" of "App behouden".~~

Niet meer gewenst: met de Teambeheer-sync (secties 6-7) als bron voor
wedstrijden is een aparte Excel-vergelijking niet meer relevant. Dit
onderdeel wordt niet gebouwd.

## 9. Database

Kerntabellen: `users`, `players`, `teams`, `seasons`, `competitions`,
`matches`, `availability`, `lineups`, `lineup_players`. Zie
`backend/app/models/` voor de daadwerkelijke implementatie (inclusief een
`audit_log`-tabel voor wijzigingsgeschiedenis).

## 10. Geschiedenis

Wie heeft wat gewijzigd? Elke wijziging in beschikbaarheid of opstelling
wordt gelogd (gebruiker, tijdstip, oude → nieuwe waarde).

## 11. Herinneringen

Spelers die nog niet gereageerd hebben krijgen een herinnering (bijv. 3 dagen
voor de wedstrijd); captains zien hoeveel spelers nog niet gereageerd hebben.

## 12. Beheer

Dashboard met kerncijfers (spelers, wedstrijden, compleet/ontbrekend,
nieuwe wedstrijden vanuit Teambeheer) en beheerschermen voor spelers, teams,
seizoenen, competities, wedstrijden, imports, gebruikers, rollen en logboek.

## 13. Mobiel én desktop

De app is mobile-first: spelers vullen beschikbaarheid vooral op hun telefoon
in, terwijl captains op desktop een uitgebreider overzicht krijgen.

## 14. Techniek

Next.js/React (frontend), Python/FastAPI (backend), PostgreSQL (database),
Linux/Docker/Nginx/HTTPS (server), dagelijkse backups met 30 dagen historie.

## 15. Migratie

Eenmalige import van de huidige Excel-planning (wedstrijden, spelers,
beschikbaarheden) naar PostgreSQL, zodat het huidige seizoen meteen in de
nieuwe applicatie staat.

## 16. MVP-fasering

**Fase 1 — werkende basis** (dit wordt nu gebouwd)

- Speler: inloggen, wedstrijden bekijken, beschikbaarheid invullen
- Captain: wedstrijden bekijken, beschikbaarheid bekijken, opstelling maken
  en publiceren
- Beheer: spelers beheren, wedstrijden beheren, Excel importeren,
  Teambeheer importeren

**Fase 2** — wijzigingslog, herinneringen, betere statistieken.
(Excel-verschilcontrole is geschrapt, zie sectie 8.)

**Fase 3** — seizoenen, automatische notificaties, uitgebreide
wedstrijdhistorie, PWA. (Volledige multi-team ondersteuning is een leuke
uitbreiding voor later, maar nu niet nodig.)

**Teambeheer-sync** (secties 6-7) — handmatige import + nachtelijke
automatische synchronisatie, gebouwd tegen de echte jaarprogramma-feed.

---

*Opmerking: de Teambeheer-feed kon aanvankelijk niet technisch geïnspecteerd
worden. Advies was om eerst de MVP rond de bestaande Excel-data te bouwen en
Teambeheer in een latere stap te koppelen — dat is ook hoe deze eerste versie
is opgezet. Inmiddels is de echte feed-structuur bekend en is de
Teambeheer-sync (secties 6-7) gebouwd.*
