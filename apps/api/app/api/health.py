"""Endpoint de salud (no requiere autenticacion)."""
from __future__ import annotations

from fastapi import APIRouter

from app import __version__

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    """Comprobacion de vida del servicio."""
    return {"status": "ok", "version": __version__}
