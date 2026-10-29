from datetime import date, time

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.enums import MatchStatus, MatchType


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True, index=True)
    season_id: Mapped[int | None] = mapped_column(ForeignKey("seasons.id"), nullable=True)
    type: Mapped[MatchType] = mapped_column(Enum(MatchType), default=MatchType.COMPETITIE, nullable=False)
    nummer: Mapped[str | None] = mapped_column(String(20), nullable=True)
    datum: Mapped[date] = mapped_column(Date, nullable=False)
    # Zodra Teambeheer een al geplande wedstrijd weer als "n.n.b." toont
    # (uitgesteld, nieuwe datum nog onbekend), kan datum niet leeg: die kolom
    # is bewust not-null (sortering/filtering op datum leunt daarop overal in
    # de app). datum blijft dus op de laatst bekende waarde staan, maar dit
    # vlag maakt dat zichtbaar in de UI zodat niemand op een verouderde datum
    # afgaat. Wordt automatisch weer False zodra er een echte datum terugkomt.
    datum_onbekend: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    tijd: Mapped[time | None] = mapped_column(Time, nullable=True)
    thuisteam: Mapped[str] = mapped_column(String(120), nullable=False)
    uitteam: Mapped[str] = mapped_column(String(120), nullable=False)
    locatie: Mapped[str | None] = mapped_column(String(120), nullable=True)
    uitslag: Mapped[str | None] = mapped_column(String(20), nullable=True)
    uitslag_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[MatchStatus] = mapped_column(Enum(MatchStatus), default=MatchStatus.GEPLAND, nullable=False)

    season: Mapped["Season"] = relationship(back_populates="matches")
    availabilities: Mapped[list["Availability"]] = relationship(
        back_populates="match", cascade="all, delete-orphan"
    )
    lineup: Mapped["Lineup"] = relationship(back_populates="match", uselist=False, cascade="all, delete-orphan")
