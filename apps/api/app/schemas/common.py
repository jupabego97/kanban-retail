"""Esquemas comunes: paginacion y respuestas genericas."""
from __future__ import annotations

from typing import Generic, List, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """Contenedor paginado estandar."""

    items: List[T]
    total: int
    page: int
    size: int
    pages: int


class MessageResponse(BaseModel):
    message: str


def build_page(items: list, total: int, page: int, size: int) -> dict:
    """Construye el dict de una pagina calculando el numero de paginas."""
    pages = (total + size - 1) // size if size else 0
    return {"items": items, "total": total, "page": page, "size": size, "pages": pages}
