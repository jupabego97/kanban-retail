"""Maquina de estados estricta del tablero de captura de demanda.

Flujo principal:
    NUEVA -> VALIDANDO -> COTIZANDO -> POR_PEDIR -> EN_CAMINO -> DISPONIBLE -> CERRADA

Ademas, cualquier estado ABIERTO puede pasar a DESCARTADA.
Los estados CERRADA y DESCARTADA son terminales.
"""
from __future__ import annotations

from typing import Dict, Set

from app.enums import OPEN_STATUSES, TERMINAL_STATUSES, DemandStatus
from app.errors import InvalidTransitionError

# Transiciones permitidas en el flujo lineal (sin contar DESCARTADA).
_LINEAR_TRANSITIONS: Dict[DemandStatus, Set[DemandStatus]] = {
    DemandStatus.NUEVA: {DemandStatus.VALIDANDO},
    DemandStatus.VALIDANDO: {DemandStatus.COTIZANDO},
    DemandStatus.COTIZANDO: {DemandStatus.POR_PEDIR},
    DemandStatus.POR_PEDIR: {DemandStatus.EN_CAMINO},
    DemandStatus.EN_CAMINO: {DemandStatus.DISPONIBLE},
    DemandStatus.DISPONIBLE: {DemandStatus.CERRADA},
    DemandStatus.CERRADA: set(),
    DemandStatus.DESCARTADA: set(),
}


def _coerce(status: object) -> DemandStatus:
    """Convierte una cadena/enum a DemandStatus, validando que exista."""
    if isinstance(status, DemandStatus):
        return status
    try:
        return DemandStatus(str(status))
    except ValueError as exc:
        raise InvalidTransitionError(
            f"Estado desconocido: {status!r}",
            details={"status": str(status)},
        ) from exc


def allowed_transitions(current: object) -> Set[DemandStatus]:
    """Devuelve el conjunto de estados alcanzables desde `current`."""
    current_status = _coerce(current)
    targets: Set[DemandStatus] = set(_LINEAR_TRANSITIONS.get(current_status, set()))
    # Desde cualquier estado abierto se puede descartar.
    if current_status in OPEN_STATUSES:
        targets.add(DemandStatus.DESCARTADA)
    return targets


def can_transition(current: object, target: object) -> bool:
    """Indica si la transicion current -> target es valida (sin levantar errores)."""
    try:
        current_status = _coerce(current)
        target_status = _coerce(target)
    except InvalidTransitionError:
        return False
    if current_status == target_status:
        return False
    return target_status in allowed_transitions(current_status)


def validate_transition(current: object, target: object) -> DemandStatus:
    """Valida la transicion; levanta InvalidTransitionError si no es permitida.

    Devuelve el estado destino como DemandStatus cuando es valido.
    """
    current_status = _coerce(current)
    target_status = _coerce(target)

    if current_status in TERMINAL_STATUSES:
        raise InvalidTransitionError(
            f"El estado {current_status.value} es terminal y no admite cambios.",
            details={"from": current_status.value, "to": target_status.value},
        )

    if current_status == target_status:
        raise InvalidTransitionError(
            "El estado destino es igual al actual.",
            details={"from": current_status.value, "to": target_status.value},
        )

    if target_status not in allowed_transitions(current_status):
        raise InvalidTransitionError(
            f"Transicion no permitida: {current_status.value} -> {target_status.value}.",
            details={
                "from": current_status.value,
                "to": target_status.value,
                "allowed": sorted(s.value for s in allowed_transitions(current_status)),
            },
        )

    return target_status
