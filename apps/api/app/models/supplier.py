"""Modelo de proveedor."""
from __future__ import annotations

from typing import Optional

from sqlmodel import Field

from app.models.base import TimestampMixin


class Supplier(TimestampMixin, table=True):
    __tablename__ = "suppliers"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, nullable=False)
    contact_phone: Optional[str] = Field(default=None)
    email: Optional[str] = Field(default=None)
    # Dias promedio de entrega del proveedor.
    lead_days: int = Field(default=0, nullable=False)
    notes: Optional[str] = Field(default=None)
