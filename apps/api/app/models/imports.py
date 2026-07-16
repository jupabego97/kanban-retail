"""Modelo de trabajos de importacion CSV."""
from __future__ import annotations

from typing import Optional

from sqlmodel import Field

from app.enums import ImportStatus
from app.models.base import TimestampMixin


class ImportJob(TimestampMixin, table=True):
    __tablename__ = "import_jobs"

    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str = Field(nullable=False)
    # Tipo de entidad importada: "products" o "suppliers".
    entity_type: str = Field(default="products", nullable=False)
    status: str = Field(default=ImportStatus.PENDING.value, index=True, nullable=False)
    rows_ok: int = Field(default=0, nullable=False)
    rows_error: int = Field(default=0, nullable=False)
    created_by_id: Optional[int] = Field(default=None, foreign_key="users.id")
    error_summary: Optional[str] = Field(default=None)
