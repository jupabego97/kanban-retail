"""Router de consulta de la bitacora de auditoria (MANAGER+)."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, func, select

from app.api.deps import Pagination, pagination_params
from app.db import get_session
from app.enums import Role
from app.models.audit import AuditLog
from app.models.user import User
from app.schemas.audit import AuditLogRead
from app.schemas.common import Page, build_page
from app.security.deps import require_roles

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=Page[AuditLogRead])
def list_audit(
    session: Session = Depends(get_session),
    pagination: Pagination = Depends(pagination_params),
    action: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    actor_id: Optional[int] = Query(None),
    _: User = Depends(require_roles(Role.OWNER, Role.MANAGER)),
) -> Page[AuditLogRead]:
    stmt = select(AuditLog)
    count_stmt = select(func.count()).select_from(AuditLog)

    filters = []
    if action:
        filters.append(AuditLog.action == action)
    if entity_type:
        filters.append(AuditLog.entity_type == entity_type)
    if actor_id is not None:
        filters.append(AuditLog.actor_id == actor_id)
    for f in filters:
        stmt = stmt.where(f)
        count_stmt = count_stmt.where(f)

    total = session.exec(count_stmt).one()
    stmt = stmt.order_by(AuditLog.id.desc()).offset(pagination.offset).limit(pagination.limit)
    items = session.exec(stmt).all()
    return build_page(items, total, pagination.page, pagination.size)
