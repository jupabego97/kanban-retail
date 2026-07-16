"""Enumeraciones del dominio.

Se definen como (str, Enum) para que se almacenen como texto en la base de datos
y sean comparables directamente con cadenas. Esto mantiene la migracion de Alembic
portable entre SQLite (tests) y PostgreSQL (produccion) sin usar tipos ENUM nativos.
"""
from __future__ import annotations

from enum import Enum


class Role(str, Enum):
    """Roles de usuario ordenados de mayor a menor privilegio."""

    OWNER = "OWNER"
    MANAGER = "MANAGER"
    OPERATOR = "OPERATOR"
    VIEWER = "VIEWER"


class DemandStatus(str, Enum):
    """Estados del tablero Kanban de captura de demanda."""

    NUEVA = "NUEVA"
    VALIDANDO = "VALIDANDO"
    COTIZANDO = "COTIZANDO"
    POR_PEDIR = "POR_PEDIR"
    EN_CAMINO = "EN_CAMINO"
    DISPONIBLE = "DISPONIBLE"
    CERRADA = "CERRADA"
    DESCARTADA = "DESCARTADA"


class DemandReason(str, Enum):
    """Motivo por el cual se registra la demanda."""

    OUT_OF_STOCK = "OUT_OF_STOCK"
    NOT_CARRIED = "NOT_CARRIED"
    NEW_RELEASE = "NEW_RELEASE"


class DemandChannel(str, Enum):
    """Canal por el que llego la solicitud del cliente."""

    STORE = "STORE"
    WHATSAPP = "WHATSAPP"
    PHONE = "PHONE"
    WEB = "WEB"
    OTHER = "OTHER"


class Priority(str, Enum):
    """Prioridad de atencion de la demanda."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class ImportStatus(str, Enum):
    """Estado de un trabajo de importacion CSV."""

    PENDING = "PENDING"
    PREVIEW = "PREVIEW"
    COMMITTED = "COMMITTED"
    FAILED = "FAILED"


# Conjunto de estados considerados "abiertos" (permiten pasar a DESCARTADA).
OPEN_STATUSES = {
    DemandStatus.NUEVA,
    DemandStatus.VALIDANDO,
    DemandStatus.COTIZANDO,
    DemandStatus.POR_PEDIR,
    DemandStatus.EN_CAMINO,
    DemandStatus.DISPONIBLE,
}

# Estados terminales que no permiten mas transiciones.
TERMINAL_STATUSES = {DemandStatus.CERRADA, DemandStatus.DESCARTADA}
