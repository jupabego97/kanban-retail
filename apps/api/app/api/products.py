"""Router CRUD de productos con busqueda por nombre/barcode/sku."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, func, or_, select

from app.api.deps import Pagination, pagination_params
from app.db import get_session
from app.enums import Role
from app.errors import DuplicateError, NotFoundError
from app.models.base import utcnow
from app.models.product import Product, ProductAlias
from app.models.user import User
from app.schemas.common import Page, build_page
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate
from app.security.deps import get_current_user, require_roles
from app.services.audit_service import record_audit

router = APIRouter(prefix="/products", tags=["products"])

_EDITORS = (Role.OWNER, Role.MANAGER, Role.OPERATOR)


def _get_product(session: Session, product_id: int) -> Product:
    product = session.get(Product, product_id)
    if product is None or product.deleted_at is not None:
        raise NotFoundError("Producto no encontrado.", details={"id": product_id})
    return product


@router.get("", response_model=Page[ProductRead])
def list_products(
    session: Session = Depends(get_session),
    pagination: Pagination = Depends(pagination_params),
    q: Optional[str] = Query(None, description="Busca por nombre, sku o barcode."),
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    _: User = Depends(get_current_user),
) -> Page[ProductRead]:
    stmt = select(Product).where(Product.deleted_at.is_(None))
    count_stmt = select(func.count()).select_from(Product).where(Product.deleted_at.is_(None))
    if q:
        like = f"%{q}%"
        cond = or_(Product.name.ilike(like), Product.sku.ilike(like), Product.barcode.ilike(like))
        stmt = stmt.where(cond)
        count_stmt = count_stmt.where(cond)
    if category:
        stmt = stmt.where(Product.category == category)
        count_stmt = count_stmt.where(Product.category == category)
    if is_active is not None:
        stmt = stmt.where(Product.is_active == is_active)
        count_stmt = count_stmt.where(Product.is_active == is_active)

    total = session.exec(count_stmt).one()
    stmt = stmt.order_by(Product.name).offset(pagination.offset).limit(pagination.limit)
    items = session.exec(stmt).all()
    return build_page(items, total, pagination.page, pagination.size)


@router.post("", response_model=ProductRead, status_code=201)
def create_product(
    payload: ProductCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles(*_EDITORS)),
) -> Product:
    exists = session.exec(
        select(Product).where(Product.sku == payload.sku, Product.deleted_at.is_(None))
    ).first()
    if exists:
        raise DuplicateError("Ya existe un producto con ese SKU.", details={"sku": payload.sku})

    data = payload.model_dump(exclude={"aliases"})
    product = Product(**data)
    session.add(product)
    session.commit()
    session.refresh(product)

    for alias in payload.aliases:
        alias = (alias or "").strip()
        if alias:
            session.add(ProductAlias(product_id=product.id, alias=alias))
    record_audit(session, actor_id=current_user.id, action="product.create", entity_type="product", entity_id=product.id)
    session.commit()
    return product


@router.get("/{product_id}", response_model=ProductRead)
def get_product(
    product_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
) -> Product:
    return _get_product(session, product_id)


@router.patch("/{product_id}", response_model=ProductRead)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles(*_EDITORS)),
) -> Product:
    product = _get_product(session, product_id)
    updates = payload.model_dump(exclude_unset=True)
    if "sku" in updates and updates["sku"] != product.sku:
        clash = session.exec(
            select(Product).where(Product.sku == updates["sku"], Product.deleted_at.is_(None))
        ).first()
        if clash:
            raise DuplicateError("Ya existe un producto con ese SKU.", details={"sku": updates["sku"]})
    for field_name, value in updates.items():
        setattr(product, field_name, value)
    product.updated_at = utcnow()
    session.add(product)
    session.commit()
    session.refresh(product)
    record_audit(session, actor_id=current_user.id, action="product.update", entity_type="product", entity_id=product.id)
    session.commit()
    return product


@router.delete("/{product_id}", status_code=204)
def delete_product(
    product_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles(Role.OWNER, Role.MANAGER)),
):
    product = _get_product(session, product_id)
    product.deleted_at = utcnow()
    product.is_active = False
    session.add(product)
    record_audit(session, actor_id=current_user.id, action="product.delete", entity_type="product", entity_id=product.id)
    session.commit()
