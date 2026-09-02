from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


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
