from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_beheer, require_captain
from app.db.session import get_db
from app.models.audit_log import AuditLog
from app.models.availability import Availability
from app.models.lineup import Lineup
from app.schemas.audit import AuditLogOut
from app.services.audit import enrich_audit_logs

router = APIRouter(prefix="/audit-log", tags=["audit-log"])


@router.get("", response_model=list[AuditLogOut], dependencies=[Depends(require_beheer)])
def list_audit_log(limit: int = 100, offset: int = 0, db: Session = Depends(get_db)):
    logs = (
        db.query(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(min(limit, 500))
        .all()
    )
    return enrich_audit_logs(db, logs)


@router.get(
    "/match/{match_id}", response_model=list[AuditLogOut], dependencies=[Depends(require_captain)]
)
def match_audit_log(match_id: int, db: Session = Depends(get_db)):
    availability_ids = [
        row.id for row in db.query(Availability.id).filter(Availability.match_id == match_id).all()
    ]
    lineup_ids = [row.id for row in db.query(Lineup.id).filter(Lineup.match_id == match_id).all()]

    query = db.query(AuditLog).filter(
        (AuditLog.entity_type == "availability") & (AuditLog.entity_id.in_(availability_ids or [-1]))
        | (AuditLog.entity_type == "lineup") & (AuditLog.entity_id.in_(lineup_ids or [-1]))
    )
    logs = query.order_by(AuditLog.created_at.desc()).all()
    return enrich_audit_logs(db, logs)
