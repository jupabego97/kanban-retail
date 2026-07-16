"""Reexporta todos los modelos para registrarlos en la metadata de SQLModel."""
from app.models.audit import AuditLog
from app.models.demand import DemandInterest, DemandRequest, StatusHistory
from app.models.imports import ImportJob
from app.models.product import Product, ProductAlias
from app.models.supplier import Supplier
from app.models.user import User

__all__ = [
    "AuditLog",
    "DemandInterest",
    "DemandRequest",
    "StatusHistory",
    "ImportJob",
    "Product",
    "ProductAlias",
    "Supplier",
    "User",
]
