# Deployen op Ubuntu Server 26.04 LTS (minimized)

Deze instructies gaan uit van een verse **Ubuntu Server 26.04 LTS**-installatie
met de **Minimized**-optie aangevinkt in de installer (dus zonder de
standaard extra pakketten, documentatie, etc.). SSL-terminatie en de
reverse-proxy naar de buitenwereld staan op een **andere server** (de
"offloader") — deze machine draait alleen de app zelf, over gewoon HTTP,
en is niet zelf verantwoordelijk voor certificaten.

De frontend proxyt `/api`-verzoeken zelf server-side door naar de backend
(zie `frontend/next.config.mjs`). Dat betekent dat de offloader maar **één**
poort op deze server hoeft te bereiken: **3000**. De backend (poort 8000)
staat niet eens open naar buiten — `docker-compose.yml` publiceert die poort
bewust niet.

## 1. Basissysteem klaarmaken

Log in als een gebruiker met sudo-rechten en zorg dat het systeem up-to-date
is en de pakketten heeft die een minimized install niet standaard meeneemt:

```bash
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install -y ca-certificates curl gnupg git ufw
```

## 2. Docker Engine + Compose plugin installeren

Officiële Docker-apt-repository toevoegen en Docker installeren (dit werkt
ongeacht de exacte codenaam van 26.04, die wordt hieronder automatisch
opgezocht):

```bash
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

sudo systemctl enable --now docker
```

Voeg je eigen gebruiker toe aan de `docker`-groep zodat je geen `sudo` nodig
hebt voor elk `docker`-commando (log daarna opnieuw in, of gebruik
`newgrp docker`):

```bash
sudo usermod -aG docker $USER
newgrp docker
```

## 3. Firewall

Alleen SSH en de poort waar de offloader op moet kunnen komen staan open.
Vervang `OFFLOADER_IP` door het echte (interne of publieke) IP-adres van de
server met de reverse-proxy/SSL:

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow OpenSSH
sudo ufw allow from OFFLOADER_IP to any port 3000 proto tcp
sudo ufw enable
sudo ufw status verbose
```

Poort 8000 (de backend) hoeft nergens in de firewall te staan — die wordt
sowieso niet gepubliceerd door Docker Compose, dus is alleen bereikbaar
vanuit de containers onderling.

## 4. Repository ophalen en configureren

```bash
sudo mkdir -p /opt/teamplanning
sudo chown $USER:$USER /opt/teamplanning
git clone https://github.com/ROosterloo1988/Teamplanning.git /opt/teamplanning
cd /opt/teamplanning
cp .env.example .env
```

Pas `.env` aan voor productie:

```bash
nano .env
```

Zet in elk geval:

- `SECRET_KEY` — een lange willekeurige string (bv. `openssl rand -hex 32`).
- `ADMIN_PASSWORD` — niet de standaardwaarde.
- `TEAM_ACCESS_PASSWORD` — het gedeelde teamwachtwoord voor de naam-kiezer.
- `NEXT_PUBLIC_API_URL` — laat op `/api` staan (de standaard); dat is precies
  wat de proxy-opzet hierboven nodig heeft.

`CORS_ORIGINS` hoef je in deze opzet niet aan te passen: omdat de browser
alleen met dit ene origin praat (de frontend proxyt `/api` zelf), speelt
CORS geen rol meer.

## 5. Starten

```bash
docker compose up -d --build
```

Dit bouwt de images, start Postgres, draait de Alembic-migraties automatisch
(via `backend/docker-entrypoint.sh`) en maakt het eerste beheerder-account en
teamwachtwoord aan. Controleer:

```bash
curl -s http://localhost:3000/api/health
# {"status":"ok"}
```

Containers herstarten vanzelf na een reboot of Docker-herstart
(`restart: unless-stopped` in `docker-compose.yml`) — een aparte systemd-unit
is niet nodig, dat regelt Docker zelf zodra `docker.service` bij het
opstarten actief is (stap 2 heeft dat al ingesteld).

## 6. Wat de offloader (de andere server) moet doen

Op deze machine hoef je niets voor SSL te doen. Op de offloader-server komt
neer:

- TLS-terminatie voor je publieke domein (bv. `gouv.jouwdomein.nl`).
- **Alle** paden (niet alleen `/api`) doorsturen naar
  `http://<IP-van-deze-server>:3000` — de frontend regelt zelf de
  doorschakeling van `/api/*` naar de backend, dus de offloader hoeft geen
  onderscheid te maken tussen paden.

Een minimale voorbeeldconfiguratie als de offloader nginx is:

```nginx
server {
    listen 443 ssl;
    server_name gouv.jouwdomein.nl;

    # ssl_certificate / ssl_certificate_key: hoort al bij de bestaande
    # offloader-configuratie op die server.

    location / {
        proxy_pass http://10.0.0.5:3000;  # IP van deze Teamplanning-server
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 7. Updaten

```bash
cd /opt/teamplanning
git pull
docker compose up -d --build
```

Nieuwe Alembic-migraties draaien automatisch mee bij het opnieuw starten van
de backend-container.

## 8. Backups

Een dagelijkse database-dump volstaat (zie functioneel ontwerp sectie 14:
dagelijkse backups, 30 dagen historie). Voorbeeld-cronjob:

```bash
sudo crontab -e
```

```cron
0 3 * * * cd /opt/teamplanning && docker compose exec -T db pg_dump -U teamplanning teamplanning | gzip > /opt/teamplanning-backups/$(date +\%F).sql.gz
find /opt/teamplanning-backups -mtime +30 -delete
```

(maak `/opt/teamplanning-backups` eenmalig aan met `mkdir -p`.)

## 9. Logs bekijken

```bash
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f db
```

## Aanbevolen minimale specificaties

Voor dit soort kleine team-app (Next.js + FastAPI + Postgres, `docker compose
build` bouwt de Next.js-productiebuild op de server zelf) is 2 vCPU en 2 GB
RAM meestal genoeg; iets meer geheugen (4 GB) geeft comfortabeler ruimte
tijdens het bouwen van images.
