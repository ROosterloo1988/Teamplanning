from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class Season(Base):
    __tablename__ = "seasons"

    id: Mapped[int] = mapped_column(primary_key=True)
    naam: Mapped[str] = mapped_column(String(50), nullable=False)
    startjaar: Mapped[int] = mapped_column(nullable=False)
    eindjaar: Mapped[int] = mapped_column(nullable=False)

    competitions: Mapped[list["Competition"]] = relationship(back_populates="season")
    matches: Mapped[list["Match"]] = relationship(back_populates="season")
