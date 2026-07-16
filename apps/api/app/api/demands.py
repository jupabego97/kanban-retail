"""Router de solicitudes de demanda: CRUD, tablero, transiciones y consolidacion."""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, func, select

from app.api.deps import Pagination, pagination_params
from app.db import get_session
from app.enums import DemandStatus, Role
from app.errors import NotFoundError
from app.models.base import utcnow
from app.models.demand import DemandRequest, StatusHistory
from app.models.user import User
from app.schemas.common import Page, build_page
from app.schemas.demand import (
    BoardColumn,
    BoardResponse,
    ConsolidateInterest,
    DemandCreate,
    DemandRead,
    DemandStatusPatch,
    DemandUpdate,
    ReorderPatch,
    StatusHistoryRead,
)
from app.security.deps import get_current_user, require_roles
from app.services import demand_service
from app.services.audit_service import record_audit

router = APIRouter(prefix="/demands", tags=["demands"])

_EDITORS = (Role.OWNER, Role.MANAGER, Role.OPERATOR)


@router.get("", response_model=Page[DemandRead])
def list_demands(
    session: Session = Depends(get_session),
    pagination: Pagination = Depends(pagination_params),
    status: Optional[DemandStatus] = None,
    reason: Optional[str] = None,
    channel: Optional[str] = None,
    assigned_to_id: Optional[int] = None,
    supplier_id: Optional[int] = None,
    q: Optional[str] = Query(None, description="Busca en el nombre libre del producto."),
    _: User = Depends(get_current_user),
) -> Page[DemandRead]:
    stmt = select(DemandRequest).where(DemandRequest.deleted_at.is_(None))
    count_stmt = select(func.count()).select_from(DemandRequest).where(DemandRequest.deleted_at.is_(None))

    filters = []
    if status is not None:
        filters.append(DemandRequest.status == status.value)
    if reason:
        filters.append(DemandRequest.reason == reason)
    if channel:
        filters.append(DemandRequest.channel == channel)
    if assigned_to_id is not None:
        filters.append(DemandRequest.assigned_to_id == assigned_to_id)
    if supplier_id is not None:
        filters.append(DemandRequest.supplier_id == supplier_id)
    if q:
        filters.append(DemandRequest.product_name_free.ilike(f"%{q}%"))

    for f in filters:
        stmt = stmt.where(f)
        count_stmt = count_stmt.where(f)

    total = session.exec(count_stmt).one()
    stmt = stmt.order_by(DemandRequest.sort_order, DemandRequest.id).offset(pagination.offset).limit(pagination.limit)
    items = session.exec(stmt).all()
    return build_page(items, total, pagination.page, pagination.size)


@router.get("/board", response_model=BoardResponse)
def board(
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
) -> BoardResponse:
    """Devuelve las tarjetas agrupadas por estado (columnas del Kanban)."""
    stmt = (
        select(DemandRequest)
        .where(DemandRequest.deleted_at.is_(None))
        .order_by(DemandRequest.sort_order, DemandRequest.id)
    )
    demands = session.exec(stmt).all()

    columns: dict[str, list] = {s.value: [] for s in DemandStatus}
    for d in demands:
        columns.setdefault(d.status, []).append(d)

    board_columns: List[BoardColumn] = [
        BoardColumn(status=s.value, items=columns.get(s.value, [])) for s in DemandStatus
    ]
    counts = {s.value: len(columns.get(s.value, [])) for s in DemandStatus}
    return BoardResponse(columns=board_columns, counts=counts)


@router.patch("/reorder")
def reorder(
    payload: ReorderPatch,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles(*_EDITORS)),
) -> dict:
    """Reordena tarjetas (y mueve de columna) en bloque.

    Se declara antes de las rutas con `/{demand_id}` para que "reorder" no se
    interprete como un id numerico.
    """
    items = [
        {"id": it.id, "sort_order": it.sort_order, "status": it.status.value if it.status else None}
        for it in payload.items
    ]
    updated = demand_service.reorder(session, items, actor_id=current_user.id)
    session.commit()
    return {"updated": updated}


@router.post("", response_model=DemandRead, status_code=201)
def create_demand(
    payload: DemandCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles(*_EDITORS)),
) -> DemandRequest:
    data = payload.model_dump()
    # Normaliza enums a su valor string para el modelo.
    for enum_field in ("reason", "channel", "priority"):
        if data.get(enum_field) is not None:
            data[enum_field] = data[enum_field].value

    # sort_order al final de la columna NUEVA.
    max_order = session.exec(
        select(func.coalesce(func.max(DemandRequest.sort_order), 0)).where(
            DemandRequest.status == DemandStatus.NUEVA.value
        )
    ).one()

    demand = DemandRequest(**data, status=DemandStatus.NUEVA.value, sort_order=(max_order or 0) + 1)
    session.add(demand)
    session.commit()
    session.refresh(demand)

    # Historial inicial de creacion.
    session.add(
        StatusHistory(
            demand_request_id=demand.id,
            from_status=None,
            to_status=DemandStatus.NUEVA.value,
            changed_by_id=current_user.id,
            note="Creacion de la solicitud",
        )
    )
    record_audit(session, actor_id=current_user.id, action="demand.create", entity_type="demand_request", entity_id=demand.id)
    session.commit()
    session.refresh(demand)
    return demand


@router.get("/{demand_id}", response_model=DemandRead)
def get_demand(
    demand_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
) -> DemandRequest:
    return demand_service.get_demand_or_404(session, demand_id)


@router.get("/{demand_id}/history", response_model=List[StatusHistoryRead])
def get_history(
    demand_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
) -> List[StatusHistory]:
    demand_service.get_demand_or_404(session, demand_id)
    stmt = (
        select(StatusHistory)
        .where(StatusHistory.demand_request_id == demand_id)
        .order_by(StatusHistory.id)
    )
    return session.exec(stmt).all()


@router.patch("/{demand_id}", response_model=DemandRead)
def update_demand(
    demand_id: int,
    payload: DemandUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles(*_EDITORS)),
) -> DemandRequest:
    demand = demand_service.get_demand_or_404(session, demand_id)
    updates = payload.model_dump(exclude_unset=True)
    for enum_field in ("reason", "channel", "priority"):
        if updates.get(enum_field) is not None:
            updates[enum_field] = updates[enum_field].value
    for field_name, value in updates.items():
        setattr(demand, field_name, value)
    demand.version += 1
    demand.updated_at = utcnow()
    session.add(demand)
    record_audit(session, actor_id=current_user.id, action="demand.update", entity_type="demand_request", entity_id=demand.id)
    session.commit()
    session.refresh(demand)
    return demand


@router.patch("/{demand_id}/status", response_model=DemandRead)
def change_status(
    demand_id: int,
    payload: DemandStatusPatch,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles(*_EDITORS)),
) -> DemandRequest:
    """Cambia el estado validando la maquina de estados y la version optimista."""
    demand = demand_service.get_demand_or_404(session, demand_id)
    demand_service.change_status(
        session,
        demand,
        payload.status.value,
        actor_id=current_user.id,
        expected_version=payload.version,
        note=payload.note,
    )
    session.commit()
    session.refresh(demand)
    return demand


@router.post("/{demand_id}/consolidate", response_model=DemandRead)
def consolidate(
    demand_id: int,
    payload: ConsolidateInterest,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles(*_EDITORS)),
) -> DemandRequest:
    """Consolida un interes adicional de cliente sobre una demanda existente."""
    demand = demand_service.get_demand_or_404(session, demand_id)
    demand_service.consolidate_interest(session, demand, actor_id=current_user.id, note=payload.note)
    session.commit()
    session.refresh(demand)
    return demand


@router.delete("/{demand_id}", status_code=204)
def delete_demand(
    demand_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles(Role.OWNER, Role.MANAGER)),
):
    demand = demand_service.get_demand_or_404(session, demand_id)
    demand.deleted_at = utcnow()
    session.add(demand)
    record_audit(session, actor_id=current_user.id, action="demand.delete", entity_type="demand_request", entity_id=demand.id)
    session.commit()
