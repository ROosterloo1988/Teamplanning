from sqlalchemy.orm import Session, joinedload

from app.models.audit_log import AuditLog
from app.models.availability import Availability
from app.models.lineup import Lineup
from app.models.user import User
from app.schemas.audit import AuditLogOut


def enrich_audit_logs(db: Session, logs: list[AuditLog]) -> list[AuditLogOut]:
    """Voegt spelers-/wedstrijdcontext toe aan ruwe audit-log-rijen voor weergave."""
    availability_ids = [l.entity_id for l in logs if l.entity_type == "availability"]
    lineup_ids = [l.entity_id for l in logs if l.entity_type == "lineup"]
    user_ids = [l.user_id for l in logs if l.user_id is not None]

    availabilities = (
        {
            a.id: a
            for a in db.query(Availability)
            .options(joinedload(Availability.match), joinedload(Availability.player))
            .filter(Availability.id.in_(availability_ids))
            .all()
        }
        if availability_ids
        else {}
    )
    lineups = (
        {
            l.id: l
            for l in db.query(Lineup)
            .options(joinedload(Lineup.match))
            .filter(Lineup.id.in_(lineup_ids))
            .all()
        }
        if lineup_ids
        else {}
    )
    users = {u.id: u for u in db.query(User).filter(User.id.in_(user_ids)).all()} if user_ids else {}

    result: list[AuditLogOut] = []
    for log in logs:
        entry = AuditLogOut(
            id=log.id,
            created_at=log.created_at,
            user_naam=users[log.user_id].naam if log.user_id in users else None,
            entity_type=log.entity_type,
            action=log.action,
            old_value=log.old_value,
            new_value=log.new_value,
        )
        if log.entity_type == "availability" and log.entity_id in availabilities:
            availability = availabilities[log.entity_id]
            entry.match_id = availability.match_id
            entry.match_datum = availability.match.datum
            entry.match_thuisteam = availability.match.thuisteam
            entry.match_uitteam = availability.match.uitteam
            entry.player_naam = availability.player.naam
        elif log.entity_type == "lineup" and log.entity_id in lineups:
            lineup = lineups[log.entity_id]
            entry.match_id = lineup.match_id
            entry.match_datum = lineup.match.datum
            entry.match_thuisteam = lineup.match.thuisteam
            entry.match_uitteam = lineup.match.uitteam
        result.append(entry)
    return result


def log_change(
    db: Session,
    *,
    user_id: int | None,
    entity_type: str,
    entity_id: int,
    action: str,
    old_value: str | None,
    new_value: str | None,
) -> None:
    """Registreer wie wat wijzigde, zie functioneel ontwerp v1 sectie 10."""
    db.add(
        AuditLog(
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            old_value=old_value,
            new_value=new_value,
        )
    )
