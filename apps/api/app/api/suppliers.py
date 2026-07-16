"""Router CRUD de proveedores."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, func, select

from app.api.deps import Pagination, pagination_params
from app.db import get_session
from app.enums import Role
from app.errors import NotFoundError
from app.models.base import utcnow
from app.models.supplier import Supplier
from app.models.user import User
from app.schemas.common import Page, build_page
from app.schemas.supplier import SupplierCreate, SupplierRead, SupplierUpdate
from app.security.deps import get_current_user, require_roles
from app.services.audit_service import record_audit

router = APIRouter(prefix="/suppliers", tags=["suppliers"])

_EDITORS = (Role.OWNER, Role.MANAGER, Role.OPERATOR)


def _get_supplier(session: Session, supplier_id: int) -> Supplier:
    supplier = session.get(Supplier, supplier_id)
    if supplier is None or supplier.deleted_at is not None:
        raise NotFoundError("Proveedor no encontrado.", details={"id": supplier_id})
    return supplier


@router.get("", response_model=Page[SupplierRead])
def list_suppliers(
    session: Session = Depends(get_session),
    pagination: Pagination = Depends(pagination_params),
    q: Optional[str] = Query(None),
    _: User = Depends(get_current_user),
) -> Page[SupplierRead]:
    stmt = select(Supplier).where(Supplier.deleted_at.is_(None))
    count_stmt = select(func.count()).select_from(Supplier).where(Supplier.deleted_at.is_(None))
    if q:
        like = f"%{q}%"
        stmt = stmt.where(Supplier.name.ilike(like))
        count_stmt = count_stmt.where(Supplier.name.ilike(like))
    total = session.exec(count_stmt).one()
    stmt = stmt.order_by(Supplier.name).offset(pagination.offset).limit(pagination.limit)
    items = session.exec(stmt).all()
    return build_page(items, total, pagination.page, pagination.size)


@router.post("", response_model=SupplierRead, status_code=201)
def create_supplier(
    payload: SupplierCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles(*_EDITORS)),
) -> Supplier:
    supplier = Supplier(**payload.model_dump())
    session.add(supplier)
    session.commit()
    session.refresh(supplier)
    record_audit(session, actor_id=current_user.id, action="supplier.create", entity_type="supplier", entity_id=supplier.id)
    session.commit()
    return supplier


@router.get("/{supplier_id}", response_model=SupplierRead)
def get_supplier(
    supplier_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
) -> Supplier:
    return _get_supplier(session, supplier_id)


@router.patch("/{supplier_id}", response_model=SupplierRead)
def update_supplier(
    supplier_id: int,
    payload: SupplierUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles(*_EDITORS)),
) -> Supplier:
    supplier = _get_supplier(session, supplier_id)
    for field_name, value in payload.model_dump(exclude_unset=True).items():
        setattr(supplier, field_name, value)
    supplier.updated_at = utcnow()
    session.add(supplier)
    session.commit()
    session.refresh(supplier)
    record_audit(session, actor_id=current_user.id, action="supplier.update", entity_type="supplier", entity_id=supplier.id)
    session.commit()
    return supplier


@router.delete("/{supplier_id}", status_code=204)
def delete_supplier(
    supplier_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles(Role.OWNER, Role.MANAGER)),
):
    supplier = _get_supplier(session, supplier_id)
    supplier.deleted_at = utcnow()
    session.add(supplier)
    record_audit(session, actor_id=current_user.id, action="supplier.delete", entity_type="supplier", entity_id=supplier.id)
    session.commit()
