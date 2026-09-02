from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class Competition(Base):
    __tablename__ = "competitions"

    id: Mapped[int] = mapped_column(primary_key=True)
    season_id: Mapped[int] = mapped_column(ForeignKey("seasons.id"), nullable=False)
    naam: Mapped[str] = mapped_column(String(120), nullable=False)
    poule: Mapped[str | None] = mapped_column(String(50), nullable=True)

    season: Mapped["Season"] = relationship(back_populates="competitions")
