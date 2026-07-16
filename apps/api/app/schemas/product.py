"""Esquemas de productos y alias."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    sku: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=300)
    barcode: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    supplier_id: Optional[int] = None
    is_active: bool = True
    aliases: List[str] = Field(default_factory=list)


class ProductUpdate(BaseModel):
    sku: Optional[str] = Field(default=None, min_length=1, max_length=100)
    name: Optional[str] = Field(default=None, min_length=1, max_length=300)
    barcode: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    supplier_id: Optional[int] = None
    is_active: Optional[bool] = None


class ProductRead(BaseModel):
    id: int
    sku: str
    barcode: Optional[str]
    name: str
    brand: Optional[str]
    category: Optional[str]
    supplier_id: Optional[int]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
