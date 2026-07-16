"""Servicio para registrar eventos en la bitacora de auditoria."""
from __future__ import annotations

from typing import Any, Optional

from sqlmodel import Session

from app.models.audit import AuditLog


def record_audit(
    session: Session,
    *,
    actor_id: Optional[int],
    action: str,
    entity_type: str,
    entity_id: Optional[int] = None,
    meta: Optional[dict[str, Any]] = None,
) -> AuditLog:
    """Crea (sin commit) una entrada de auditoria. El caller hace commit."""
    entry = AuditLog(
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        meta=meta,
    )
    session.add(entry)
    return entry
