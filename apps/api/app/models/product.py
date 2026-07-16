"""Modelos de producto y sus alias."""
from __future__ import annotations

from typing import Optional

from sqlmodel import Field

from app.models.base import TimestampMixin


class Product(TimestampMixin, table=True):
    __tablename__ = "products"

    id: Optional[int] = Field(default=None, primary_key=True)
    sku: str = Field(index=True, unique=True, nullable=False)
    barcode: Optional[str] = Field(default=None, index=True)
    name: str = Field(index=True, nullable=False)
    brand: Optional[str] = Field(default=None, index=True)
    category: Optional[str] = Field(default=None, index=True)
    supplier_id: Optional[int] = Field(default=None, foreign_key="suppliers.id", index=True)
    is_active: bool = Field(default=True, nullable=False)


class ProductAlias(TimestampMixin, table=True):
    """Nombres alternativos con los que los clientes piden un producto."""

    __tablename__ = "product_aliases"

    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="products.id", index=True, nullable=False)
    alias: str = Field(index=True, nullable=False)
