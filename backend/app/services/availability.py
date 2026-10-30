from sqlalchemy.orm import Session

from app.models.availability import Availability
from app.models.enums import AvailabilityStatus


def reset_availability(db: Session, match_id: int) -> None:
    """Zet alle beschikbaarheid voor een wedstrijd terug naar 'geen antwoord'.

    Nodig zodra de datum van een wedstrijd echt verandert (of weer onbekend
    wordt): een eerder "ja" of "nee" sloeg op de oude datum en zegt niets
    over de nieuwe — dat zou spelers juist op het verkeerde been zetten.
    """
    db.query(Availability).filter(Availability.match_id == match_id).update(
        {Availability.status: AvailabilityStatus.NO_RESPONSE}, synchronize_session=False
    )
