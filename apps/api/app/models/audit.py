"""Modelo de bitacora de auditoria."""
from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import JSON, Column
from sqlmodel import Field

from app.models.base import TimestampMixin


class AuditLog(TimestampMixin, table=True):
    __tablename__ = "audit_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    actor_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True)
    action: str = Field(index=True, nullable=False)
    entity_type: str = Field(index=True, nullable=False)
    entity_id: Optional[int] = Field(default=None, index=True)
    # Se llama "meta" en Python (metadata esta reservado por SQLAlchemy).
    # Se serializa como JSON (portable entre SQLite y PostgreSQL).
    meta: Optional[dict[str, Any]] = Field(default=None, sa_column=Column("meta", JSON))
