"""Eenmalig een beheerder-account aanmaken. Uitvoeren met: python -m app.initial_data"""
import os

from app.core.security import hash_password

# Importeer via app.db.base (niet app.models.user) zodat alle modellen
# geregistreerd zijn voor SQLAlchemy's mappers — User.player verwijst naar
# Player via een stringnaam die anders onopgelost blijft in dit losstaande
# script.
from app.db.base import User
from app.db.session import SessionLocal
from app.models.enums import UserRole


def main() -> None:
    email = os.environ.get("ADMIN_EMAIL", "admin@teamplanning.nl")
    password = os.environ.get("ADMIN_PASSWORD", "changeme")
    naam = os.environ.get("ADMIN_NAAM", "Beheerder")

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print(f"Gebruiker {email} bestaat al, overslaan.")
            return

        user = User(
            naam=naam,
            email=email,
            hashed_password=hash_password(password),
            rol=UserRole.BEHEER,
            actief=True,
        )
        db.add(user)
        db.commit()
        print(f"Beheerder-account aangemaakt: {email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
