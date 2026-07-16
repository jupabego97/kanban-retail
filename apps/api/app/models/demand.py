"""Modelos del nucleo del negocio: solicitudes de demanda e historial."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field

from app.enums import DemandChannel, DemandReason, DemandStatus, Priority
from app.models.base import TimestampMixin, utcnow


class DemandRequest(TimestampMixin, table=True):
    """Solicitud de demanda insatisfecha (tarjeta del tablero Kanban)."""

    __tablename__ = "demand_requests"

    id: Optional[int] = Field(default=None, primary_key=True)

    # El producto puede estar en el catalogo (product_id) o describirse libremente.
    product_id: Optional[int] = Field(default=None, foreign_key="products.id", index=True)
    product_name_free: Optional[str] = Field(default=None)
    variant: Optional[str] = Field(default=None)

    quantity: int = Field(default=1, nullable=False)
    reason: str = Field(default=DemandReason.OUT_OF_STOCK.value, index=True, nullable=False)
    channel: str = Field(default=DemandChannel.STORE.value, index=True, nullable=False)
    status: str = Field(default=DemandStatus.NUEVA.value, index=True, nullable=False)
    priority: str = Field(default=Priority.MEDIUM.value, index=True, nullable=False)

    notes: Optional[str] = Field(default=None)

    # Datos de contacto del cliente (opcionales, requieren consentimiento).
    customer_contact: Optional[str] = Field(default=None)
    customer_consent: bool = Field(default=False, nullable=False)

    assigned_to_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True)
    supplier_id: Optional[int] = Field(default=None, foreign_key="suppliers.id", index=True)

    evidence_url: Optional[str] = Field(default=None)

    # Orden dentro de la columna del tablero.
    sort_order: int = Field(default=0, nullable=False)

    # Control de concurrencia optimista: se incrementa en cada actualizacion.
    version: int = Field(default=1, nullable=False)

    # Consolidacion: agrupa varias tarjetas en una misma oportunidad.
    opportunity_id: Optional[int] = Field(default=None, index=True)


class DemandInterest(TimestampMixin, table=True):
    """Interes adicional de un cliente sobre una demanda ya existente."""

    __tablename__ = "demand_interests"

    id: Optional[int] = Field(default=None, primary_key=True)
    demand_request_id: int = Field(foreign_key="demand_requests.id", index=True, nullable=False)
    note: Optional[str] = Field(default=None)
    created_by_id: Optional[int] = Field(default=None, foreign_key="users.id")


class StatusHistory(TimestampMixin, table=True):
    """Registro inmutable de cada cambio de estado de una demanda."""

    __tablename__ = "status_history"

    id: Optional[int] = Field(default=None, primary_key=True)
    demand_request_id: int = Field(foreign_key="demand_requests.id", index=True, nullable=False)
    from_status: Optional[str] = Field(default=None)
    to_status: str = Field(nullable=False)
    changed_by_id: Optional[int] = Field(default=None, foreign_key="users.id")
    note: Optional[str] = Field(default=None)
