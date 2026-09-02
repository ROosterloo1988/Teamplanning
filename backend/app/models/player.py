from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), unique=True, nullable=True)
    naam: Mapped[str] = mapped_column(String(120), nullable=False)
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"), nullable=True)

    user: Mapped["User"] = relationship(back_populates="player")
    team: Mapped["Team"] = relationship(back_populates="players")
    availabilities: Mapped[list["Availability"]] = relationship(back_populates="player")
