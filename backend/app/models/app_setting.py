from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


class AppSetting(Base):
    """Enkele instellingenrij voor de hele app (single-row table, id=1).

    Bevat het gedeelde teamwachtwoord dat de naam-kiezer beschermt, zie
    het inlogontwerp: eerst het teamwachtwoord, dan 'Ik ben: [naam]',
    met een persoonlijk ontgrendelwachtwoord voor captain/beheer.
    """

    __tablename__ = "app_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    team_password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
