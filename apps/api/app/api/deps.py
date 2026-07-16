"""Dependencias compartidas por los routers (paginacion)."""
from __future__ import annotations

from dataclasses import dataclass

from fastapi import Query


@dataclass
class Pagination:
    page: int
    size: int

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size

    @property
    def limit(self) -> int:
        return self.size


def pagination_params(
    page: int = Query(1, ge=1, description="Numero de pagina (1-indexado)."),
    size: int = Query(20, ge=1, le=200, description="Tamano de pagina."),
) -> Pagination:
    return Pagination(page=page, size=size)
