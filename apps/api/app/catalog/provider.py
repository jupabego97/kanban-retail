"""Interfaz abstracta de proveedor de catalogo e implementacion CSV manual.

Permite desacoplar el origen de datos del catalogo (CSV, ERP, API externa...).
Para la v1 se implementa `ManualCsvCatalogProvider`, que lee productos desde
un CSV con columnas: sku, name, barcode, brand, category.
"""
from __future__ import annotations

import csv
import io
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Iterable, List, Optional


@dataclass
class CatalogProduct:
    """Representacion neutral de un producto en el catalogo."""

    sku: str
    name: str
    barcode: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    aliases: List[str] = field(default_factory=list)


class CatalogProvider(ABC):
    """Contrato que deben cumplir los proveedores de catalogo."""

    @abstractmethod
    def list_products(self) -> Iterable[CatalogProduct]:
        """Devuelve todos los productos del catalogo."""
        raise NotImplementedError

    @abstractmethod
    def search(self, query: str) -> List[CatalogProduct]:
        """Busca productos por nombre, sku o codigo de barras."""
        raise NotImplementedError


class ManualCsvCatalogProvider(CatalogProvider):
    """Proveedor de catalogo basado en un CSV cargado manualmente."""

    REQUIRED_COLUMNS = {"sku", "name"}

    def __init__(self, products: Optional[List[CatalogProduct]] = None) -> None:
        self._products: List[CatalogProduct] = products or []

    @classmethod
    def from_csv_text(cls, text: str) -> "ManualCsvCatalogProvider":
        """Construye el proveedor a partir del contenido de un CSV."""
        reader = csv.DictReader(io.StringIO(text))
        products: List[CatalogProduct] = []
        for row in reader:
            normalized = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
            sku = normalized.get("sku", "")
            name = normalized.get("name", "")
            if not sku or not name:
                continue
            products.append(
                CatalogProduct(
                    sku=sku,
                    name=name,
                    barcode=normalized.get("barcode") or None,
                    brand=normalized.get("brand") or None,
                    category=normalized.get("category") or None,
                )
            )
        return cls(products)

    def list_products(self) -> Iterable[CatalogProduct]:
        return list(self._products)

    def search(self, query: str) -> List[CatalogProduct]:
        q = (query or "").strip().lower()
        if not q:
            return list(self._products)
        results = []
        for p in self._products:
            haystack = " ".join(filter(None, [p.sku, p.name, p.barcode or ""])).lower()
            if q in haystack:
                results.append(p)
        return results
