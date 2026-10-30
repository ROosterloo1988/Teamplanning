from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class TeambeheerConfig(Base):
    """Koppeling met de Teambeheer SDC jaarprogramma-feed, per seizoen.

    Zie functioneel ontwerp v1 secties 6 (import) en 7 (automatische sync).
    """

    __tablename__ = "teambeheer_configs"

    id: Mapped[int] = mapped_column(primary_key=True)
    season_id: Mapped[int] = mapped_column(ForeignKey("seasons.id"), unique=True, nullable=False)
    bond_id: Mapped[int] = mapped_column(Integer, nullable=False)
    poule: Mapped[str] = mapped_column(String(20), nullable=False)
    team_id: Mapped[int] = mapped_column(Integer, nullable=False)
    team_naam: Mapped[str | None] = mapped_column(String(120), nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_sync_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    last_sync_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    season: Mapped["Season"] = relationship()
