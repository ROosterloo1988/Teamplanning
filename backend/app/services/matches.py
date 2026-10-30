from sqlalchemy.orm import Session

from app.models.availability import Availability
from app.models.enums import AvailabilityStatus
from app.models.lineup import Lineup, LineupPlayer
from app.models.match import Match
from app.models.notification import Notification


class MatchMergeError(Exception):
    """Twee wedstrijden konden niet worden samengevoegd."""


def merge_matches(db: Session, keep: Match, duplicate: Match) -> Match:
    """Voegt `duplicate` in `keep` en verwijdert de dubbele wedstrijd
    daarna. Gebeurt vooral na een Teambeheer-sync die een handmatig
    ingevulde wedstrijd niet herkende (bv. een afwijkende teamnaam) en 'm
    daardoor een tweede keer aanmaakte.

    Beschikbaarheid en opstelling gaan niet verloren: een al ingevuld
    antwoord op de dubbele wedstrijd wordt overgenomen voor spelers die op
    de wedstrijd die je houdt nog "geen antwoord" hadden staan (of nog geen
    rij), en een opstelling op de dubbele wedstrijd wordt overgenomen of
    samengevoegd als er op de andere ook al een stond.
    """
    if keep.id == duplicate.id:
        raise MatchMergeError("Kan een wedstrijd niet met zichzelf samenvoegen")

    keep_availability_by_player = {
        a.player_id: a for a in db.query(Availability).filter(Availability.match_id == keep.id)
    }
    for dup_avail in db.query(Availability).filter(Availability.match_id == duplicate.id):
        keep_avail = keep_availability_by_player.get(dup_avail.player_id)
        if keep_avail is None:
            db.add(Availability(match_id=keep.id, player_id=dup_avail.player_id, status=dup_avail.status))
        elif keep_avail.status == AvailabilityStatus.NO_RESPONSE and dup_avail.status != AvailabilityStatus.NO_RESPONSE:
            keep_avail.status = dup_avail.status

    dup_lineup = db.query(Lineup).filter(Lineup.match_id == duplicate.id).first()
    if dup_lineup:
        keep_lineup = db.query(Lineup).filter(Lineup.match_id == keep.id).first()
        if keep_lineup is None:
            dup_lineup.match_id = keep.id
        else:
            existing_player_ids = {lp.player_id for lp in keep_lineup.players}
            for lp in dup_lineup.players:
                if lp.player_id not in existing_player_ids:
                    db.add(LineupPlayer(lineup_id=keep_lineup.id, player_id=lp.player_id))
            if dup_lineup.published and not keep_lineup.published:
                keep_lineup.published = True
                keep_lineup.published_at = dup_lineup.published_at
            db.delete(dup_lineup)

    # Alleen aanvullen wat op de wedstrijd die je houdt nog leeg is — een
    # waarde die daar al staat (ook als die afwijkt) blijft met rust.
    for field in ("locatie", "uitslag", "uitslag_url", "nummer"):
        if getattr(keep, field) is None and getattr(duplicate, field) is not None:
            setattr(keep, field, getattr(duplicate, field))

    # external_id is unique, dus eerst los van de dubbele wedstrijd maken
    # voordat 'm op de overgebleven wedstrijd gezet wordt — zonder deze
    # overname herkent de volgende Teambeheer-sync de overgebleven wedstrijd
    # niet en maakt hij 'm gewoon weer een keer aan.
    duplicate_external_id = duplicate.external_id
    duplicate.external_id = None
    db.flush()
    if keep.external_id is None and duplicate_external_id is not None:
        keep.external_id = duplicate_external_id

    # Notificatiehistorie laten verwijzen naar de overgebleven wedstrijd in
    # plaats van naar een straks niet-bestaande id.
    db.query(Notification).filter(Notification.match_id == duplicate.id).update(
        {Notification.match_id: keep.id}, synchronize_session=False
    )

    db.delete(duplicate)
    db.commit()
    db.refresh(keep)
    return keep
