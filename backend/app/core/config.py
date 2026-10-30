from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "Teamplanning"
    API_V1_PREFIX: str = "/api"

    DATABASE_URL: str = "postgresql+psycopg2://teamplanning:teamplanning@db:5432/teamplanning"

    SECRET_KEY: str = "change-me-in-production"
    # Beide bewust ruim: dit is een team-app op eigen toestellen (vaak als
    # PWA geinstalleerd), niet een gedeelde/publieke computer — spelers en
    # captain/beheer moeten niet steeds opnieuw hun wachtwoord hoeven in te
    # typen. 1 jaar; "Uitloggen" logt nog steeds direct uit.
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 365  # 1 jaar
    TEAM_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 365  # 1 jaar: alleen een "voordeur", geen echte login
    ALGORITHM: str = "HS256"

    # Gedeeld teamwachtwoord voor de naam-kiezer (bootstrap-waarde, zie
    # app.initial_data — wijzigbaar via Beheer > Instellingen).
    TEAM_ACCESS_PASSWORD: str = "degouv"

    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # Aantal dagen voor de wedstrijd waarop herinneringen actief worden, zie
    # functioneel ontwerp v1 sectie 11.
    REMINDER_DAYS_BEFORE: int = 3

    # Web Push (VAPID) — voor herinneringen op het toestel zelf, zie
    # functioneel ontwerp v1 sectie 11/16. Leeg (geen sleutels) betekent:
    # push staat uit, de rest van de app werkt gewoon door. Genereer een
    # sleutelpaar met bv. `vapid --gen` (py-vapid) en zet ze in .env.
    VAPID_PUBLIC_KEY: str = ""
    VAPID_PRIVATE_KEY: str = ""
    VAPID_CLAIMS_EMAIL: str = "mailto:info@degouv.nl"

    # Teambeheer SDC jaarprogramma-feed (ontwerp secties 6 en 7).
    TEAMBEHEER_BASE_URL: str = "https://feeds.teambeheer.nl"
    TEAMBEHEER_AUTO_SYNC: bool = True
    TEAMBEHEER_SYNC_HOUR: int = 3
    TEAMBEHEER_SYNC_MINUTE: int = 30


settings = Settings()
