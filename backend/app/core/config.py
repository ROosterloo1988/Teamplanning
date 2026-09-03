from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "Teamplanning"
    API_V1_PREFIX: str = "/api"

    DATABASE_URL: str = "postgresql+psycopg2://teamplanning:teamplanning@db:5432/teamplanning"

    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    ALGORITHM: str = "HS256"

    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # Aantal dagen voor de wedstrijd waarop herinneringen actief worden, zie
    # functioneel ontwerp v1 sectie 11.
    REMINDER_DAYS_BEFORE: int = 3


settings = Settings()
