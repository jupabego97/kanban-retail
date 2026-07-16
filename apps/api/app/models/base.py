"""Mixins comunes para los modelos (timestamps y soft delete)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    """Fecha/hora actual en UTC (con tzinfo)."""
    return datetime.now(timezone.utc)


class TimestampMixin(SQLModel):
    """Aporta created_at, updated_at y deleted_at (soft delete)."""

    created_at: datetime = Field(default_factory=utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=utcnow, nullable=False)
    # deleted_at != None indica que el registro fue borrado logicamente.
    deleted_at: Optional[datetime] = Field(default=None, index=True)

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
