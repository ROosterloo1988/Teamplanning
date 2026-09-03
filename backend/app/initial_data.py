"""Eenmalig een beheerder-account + teamwachtwoord aanmaken.

Uitvoeren met: python -m app.initial_data
"""
import os

from app.core.config import settings
from app.core.security import hash_password

# Importeer via app.db.base (niet app.models.user) zodat alle modellen
# geregistreerd zijn voor SQLAlchemy's mappers — User.player verwijst naar
# Player via een stringnaam die anders onopgelost blijft in dit losstaande
# script.
from app.db.base import User
from app.db.session import SessionLocal
from app.models.app_setting import AppSetting
from app.models.enums import UserRole


def seed_admin(db) -> None:
    email = os.environ.get("ADMIN_EMAIL", "admin@teamplanning.nl")
    password = os.environ.get("ADMIN_PASSWORD", "changeme")
    naam = os.environ.get("ADMIN_NAAM", "Beheerder")

    if db.query(User).filter(User.email == email).first():
        print(f"Gebruiker {email} bestaat al, overslaan.")
        return

    user = User(
        naam=naam,
        email=email,
        # Dit wachtwoord is meteen ook het ontgrendelwachtwoord voor de
        # naam-kiezer (Beheerder-rol vereist er een).
        hashed_password=hash_password(password),
        rol=UserRole.BEHEER,
        actief=True,
    )
    db.add(user)
    db.commit()
    print(f"Beheerder-account aangemaakt: {email}")


def seed_team_password(db) -> None:
    if db.query(AppSetting).first():
        print("Teamwachtwoord bestaat al, overslaan.")
        return

    db.add(AppSetting(team_password_hash=hash_password(settings.TEAM_ACCESS_PASSWORD)))
    db.commit()
    print("Teamwachtwoord ingesteld (TEAM_ACCESS_PASSWORD).")


def main() -> None:
    db = SessionLocal()
    try:
        seed_admin(db)
        seed_team_password(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
