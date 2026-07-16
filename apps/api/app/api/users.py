"""Router de gestion de usuarios (solo OWNER/MANAGER)."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, func, select

from app.api.deps import Pagination, pagination_params
from app.db import get_session
from app.enums import Role
from app.errors import DuplicateError, NotFoundError, PermissionError_
from app.models.base import utcnow
from app.models.user import User
from app.schemas.common import Page, build_page
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.security.deps import get_current_user, require_roles
from app.security.password import hash_password
from app.services.audit_service import record_audit

router = APIRouter(prefix="/users", tags=["users"])

_MANAGERS = (Role.OWNER, Role.MANAGER)


def _get_active_user(session: Session, user_id: int) -> User:
    user = session.get(User, user_id)
    if user is None or user.deleted_at is not None:
        raise NotFoundError("Usuario no encontrado.", details={"id": user_id})
    return user


@router.get("", response_model=Page[UserRead])
def list_users(
    session: Session = Depends(get_session),
    pagination: Pagination = Depends(pagination_params),
    q: Optional[str] = Query(None, description="Filtro por nombre o email."),
    role: Optional[Role] = None,
    is_active: Optional[bool] = None,
    _: User = Depends(require_roles(*_MANAGERS)),
) -> Page[UserRead]:
    stmt = select(User).where(User.deleted_at.is_(None))
    count_stmt = select(func.count()).select_from(User).where(User.deleted_at.is_(None))

    if q:
        like = f"%{q}%"
        cond = (User.name.ilike(like)) | (User.email.ilike(like))
        stmt = stmt.where(cond)
        count_stmt = count_stmt.where(cond)
    if role is not None:
        stmt = stmt.where(User.role == role.value)
        count_stmt = count_stmt.where(User.role == role.value)
    if is_active is not None:
        stmt = stmt.where(User.is_active == is_active)
        count_stmt = count_stmt.where(User.is_active == is_active)

    total = session.exec(count_stmt).one()
    stmt = stmt.order_by(User.id).offset(pagination.offset).limit(pagination.limit)
    items = session.exec(stmt).all()
    return build_page(items, total, pagination.page, pagination.size)


@router.post("", response_model=UserRead, status_code=201)
def create_user(
    payload: UserCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles(*_MANAGERS)),
) -> User:
    # Un MANAGER no puede crear un OWNER.
    if payload.role == Role.OWNER and current_user.role != Role.OWNER.value:
        raise PermissionError_("Solo un OWNER puede crear usuarios OWNER.")

    exists = session.exec(select(User).where(User.email == payload.email)).first()
    if exists:
        raise DuplicateError("Ya existe un usuario con ese email.", details={"email": payload.email})

    user = User(
        email=payload.email,
        name=payload.name,
        password_hash=hash_password(payload.password),
        role=payload.role.value,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    record_audit(session, actor_id=current_user.id, action="user.create", entity_type="user", entity_id=user.id)
    session.commit()
    return user


@router.get("/{user_id}", response_model=UserRead)
def get_user(
    user_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(require_roles(*_MANAGERS)),
) -> User:
    return _get_active_user(session, user_id)


@router.patch("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    payload: UserUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles(*_MANAGERS)),
) -> User:
    user = _get_active_user(session, user_id)

    if payload.role is not None and payload.role == Role.OWNER and current_user.role != Role.OWNER.value:
        raise PermissionError_("Solo un OWNER puede asignar el rol OWNER.")

    if payload.name is not None:
        user.name = payload.name
    if payload.role is not None:
        user.role = payload.role.value
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.password is not None:
        user.password_hash = hash_password(payload.password)
    user.updated_at = utcnow()

    session.add(user)
    session.commit()
    session.refresh(user)
    record_audit(session, actor_id=current_user.id, action="user.update", entity_type="user", entity_id=user.id)
    session.commit()
    return user


@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles(*_MANAGERS)),
):
    user = _get_active_user(session, user_id)
    if user.id == current_user.id:
        raise PermissionError_("No puede eliminar su propia cuenta.")
    if user.role == Role.OWNER.value and current_user.role != Role.OWNER.value:
        raise PermissionError_("Solo un OWNER puede eliminar a otro OWNER.")

    # Soft delete: marca la fecha de borrado y desactiva.
    user.deleted_at = utcnow()
    user.is_active = False
    session.add(user)
    record_audit(session, actor_id=current_user.id, action="user.delete", entity_type="user", entity_id=user.id)
    session.commit()
