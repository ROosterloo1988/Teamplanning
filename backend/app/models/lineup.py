from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class Lineup(Base):
    __tablename__ = "lineups"

    id: Mapped[int] = mapped_column(primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"), unique=True, nullable=False)
    published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    match: Mapped["Match"] = relationship(back_populates="lineup")
    players: Mapped[list["LineupPlayer"]] = relationship(back_populates="lineup", cascade="all, delete-orphan")


class LineupPlayer(Base):
    __tablename__ = "lineup_players"

    lineup_id: Mapped[int] = mapped_column(ForeignKey("lineups.id"), primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), primary_key=True)

    lineup: Mapped["Lineup"] = relationship(back_populates="players")
    player: Mapped["Player"] = relationship()
