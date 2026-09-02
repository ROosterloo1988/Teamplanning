from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True)
    naam: Mapped[str] = mapped_column(String(120), nullable=False)
    vereniging: Mapped[str | None] = mapped_column(String(120), nullable=True)

    players: Mapped[list["Player"]] = relationship(back_populates="team")
