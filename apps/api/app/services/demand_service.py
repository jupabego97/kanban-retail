"""Logica de negocio de las solicitudes de demanda.

Incluye cambios de estado (con la maquina de estados), control de concurrencia
optimista por version, reordenamiento en el tablero y consolidacion de intereses.
"""
from __future__ import annotations

from typing import List, Optional

from sqlmodel import Session

from app.enums import DemandStatus
from app.errors import NotFoundError, VersionConflictError
from app.models.base import utcnow
from app.models.demand import DemandInterest, DemandRequest, StatusHistory
from app.services.audit_service import record_audit
from app.state_machine import validate_transition


def get_demand_or_404(session: Session, demand_id: int) -> DemandRequest:
    demand = session.get(DemandRequest, demand_id)
    if demand is None or demand.deleted_at is not None:
        raise NotFoundError("La solicitud de demanda no existe.", details={"id": demand_id})
    return demand


def change_status(
    session: Session,
    demand: DemandRequest,
    target_status: str,
    *,
    actor_id: Optional[int],
    expected_version: Optional[int] = None,
    note: Optional[str] = None,
) -> DemandRequest:
    """Cambia el estado validando la transicion y la version optimista.

    Registra StatusHistory y auditoria. El commit lo hace el caller.
    """
    # Control de concurrencia optimista: la version enviada debe coincidir.
    if expected_version is not None and expected_version != demand.version:
        raise VersionConflictError(
            "La solicitud fue modificada por otro usuario. Recargue e intente de nuevo.",
            details={"expected": expected_version, "actual": demand.version},
        )

    from_status = demand.status
    # Valida la transicion segun la maquina de estados estricta.
    new_status: DemandStatus = validate_transition(from_status, target_status)

    demand.status = new_status.value
    demand.version += 1
    demand.updated_at = utcnow()
    session.add(demand)

    history = StatusHistory(
        demand_request_id=demand.id,
        from_status=from_status,
        to_status=new_status.value,
        changed_by_id=actor_id,
        note=note,
    )
    session.add(history)

    record_audit(
        session,
        actor_id=actor_id,
        action="demand.status_change",
        entity_type="demand_request",
        entity_id=demand.id,
        meta={"from": from_status, "to": new_status.value},
    )
    return demand


def reorder(
    session: Session,
    items: List[dict],
    *,
    actor_id: Optional[int],
) -> int:
    """Actualiza sort_order (y opcionalmente status) de varias tarjetas.

    `items` es una lista de dicts: {"id": int, "sort_order": int, "status": str?}.
    Devuelve la cantidad de tarjetas actualizadas.
    """
    updated = 0
    for item in items:
        demand = session.get(DemandRequest, item["id"])
        if demand is None or demand.deleted_at is not None:
            continue
        demand.sort_order = int(item.get("sort_order", demand.sort_order))
        # Mover de columna implica un cambio de estado validado.
        new_status = item.get("status")
        if new_status and new_status != demand.status:
            from_status = demand.status
            validated = validate_transition(from_status, new_status)
            demand.status = validated.value
            session.add(
                StatusHistory(
                    demand_request_id=demand.id,
                    from_status=from_status,
                    to_status=validated.value,
                    changed_by_id=actor_id,
                    note="Reorden en el tablero",
                )
            )
        demand.version += 1
        demand.updated_at = utcnow()
        session.add(demand)
        updated += 1

    record_audit(
        session,
        actor_id=actor_id,
        action="demand.reorder",
        entity_type="demand_request",
        entity_id=None,
        meta={"count": updated},
    )
    return updated


def consolidate_interest(
    session: Session,
    demand: DemandRequest,
    *,
    actor_id: Optional[int],
    note: Optional[str] = None,
) -> DemandInterest:
    """Registra un interes adicional de otro cliente sobre la misma demanda.

    Consolidar suma "peso" a la demanda sin crear tarjetas duplicadas: incrementa
    la cantidad total solicitada y guarda una nota de interes.
    """
    interest = DemandInterest(
        demand_request_id=demand.id,
        note=note,
        created_by_id=actor_id,
    )
    session.add(interest)

    # Cada interes adicional suma una unidad a la cantidad total demandada.
    demand.quantity += 1
    demand.version += 1
    demand.updated_at = utcnow()
    session.add(demand)

    record_audit(
        session,
        actor_id=actor_id,
        action="demand.consolidate_interest",
        entity_type="demand_request",
        entity_id=demand.id,
        meta={"note": note},
    )
    return interest
