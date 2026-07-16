"""Esquemas de auditoria."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class AuditLogRead(BaseModel):
    id: int
    actor_id: Optional[int]
    action: str
    entity_type: str
    entity_id: Optional[int]
    meta: Optional[dict[str, Any]]
    created_at: datetime

    model_config = {"from_attributes": True}
