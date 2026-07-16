"""Esquemas de solicitudes de demanda."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, model_validator

from app.enums import DemandChannel, DemandReason, DemandStatus, Priority


class DemandCreate(BaseModel):
    product_id: Optional[int] = None
    product_name_free: Optional[str] = None
    variant: Optional[str] = None
    quantity: int = Field(default=1, ge=1)
    reason: DemandReason = DemandReason.OUT_OF_STOCK
    channel: DemandChannel = DemandChannel.STORE
    priority: Priority = Priority.MEDIUM
    notes: Optional[str] = None
    customer_contact: Optional[str] = None
    customer_consent: bool = False
    assigned_to_id: Optional[int] = None
    supplier_id: Optional[int] = None
    evidence_url: Optional[str] = None

    @model_validator(mode="after")
    def _check_product(self) -> "DemandCreate":
        # Debe indicarse un producto del catalogo o un nombre libre.
        if self.product_id is None and not (self.product_name_free or "").strip():
            raise ValueError("Debe indicar product_id o product_name_free.")
        return self


class DemandUpdate(BaseModel):
    product_id: Optional[int] = None
    product_name_free: Optional[str] = None
    variant: Optional[str] = None
    quantity: Optional[int] = Field(default=None, ge=1)
    reason: Optional[DemandReason] = None
    channel: Optional[DemandChannel] = None
    priority: Optional[Priority] = None
    notes: Optional[str] = None
    customer_contact: Optional[str] = None
    customer_consent: Optional[bool] = None
    assigned_to_id: Optional[int] = None
    supplier_id: Optional[int] = None
    evidence_url: Optional[str] = None


class DemandStatusPatch(BaseModel):
    """Cambio de estado con verificacion de version optimista."""

    status: DemandStatus
    version: int = Field(ge=1, description="Version esperada de la tarjeta.")
    note: Optional[str] = None


class ReorderItem(BaseModel):
    id: int
    sort_order: int
    status: Optional[DemandStatus] = None


class ReorderPatch(BaseModel):
    items: List[ReorderItem]


class ConsolidateInterest(BaseModel):
    note: Optional[str] = None


class DemandRead(BaseModel):
    id: int
    product_id: Optional[int]
    product_name_free: Optional[str]
    variant: Optional[str]
    quantity: int
    reason: str
    channel: str
    status: str
    priority: str
    notes: Optional[str]
    customer_contact: Optional[str]
    customer_consent: bool
    assigned_to_id: Optional[int]
    supplier_id: Optional[int]
    evidence_url: Optional[str]
    sort_order: int
    version: int
    opportunity_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class StatusHistoryRead(BaseModel):
    id: int
    demand_request_id: int
    from_status: Optional[str]
    to_status: str
    changed_by_id: Optional[int]
    note: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class BoardColumn(BaseModel):
    status: str
    items: List[DemandRead]


class BoardResponse(BaseModel):
    columns: List[BoardColumn]
    counts: Dict[str, int]
