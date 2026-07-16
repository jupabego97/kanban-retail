"""Esquemas de proveedores."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SupplierCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    contact_phone: Optional[str] = None
    email: Optional[str] = None
    lead_days: int = Field(default=0, ge=0)
    notes: Optional[str] = None


class SupplierUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    contact_phone: Optional[str] = None
    email: Optional[str] = None
    lead_days: Optional[int] = Field(default=None, ge=0)
    notes: Optional[str] = None


class SupplierRead(BaseModel):
    id: int
    name: str
    contact_phone: Optional[str]
    email: Optional[str]
    lead_days: int
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
