"""Dependencias de autenticacion y autorizacion (RBAC)."""
from __future__ import annotations

from typing import Iterable

from fastapi import Depends, Request
from sqlmodel import Session, select

from app.config import settings
from app.db import get_session
from app.enums import Role
from app.errors import AuthenticationError, PermissionError_
from app.models.user import User
from app.security.session import read_session_token


def get_current_user(request: Request, session: Session = Depends(get_session)) -> User:
    """Obtiene el usuario autenticado a partir de la cookie de sesion."""
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    user_id = read_session_token(token) if token else None
    if user_id is None:
        raise AuthenticationError("No autenticado o sesion expirada.")

    user = session.get(User, user_id)
    if user is None or user.deleted_at is not None or not user.is_active:
        raise AuthenticationError("Usuario no valido o inactivo.")
    return user


def require_roles(*roles: Role):
    """Fabrica de dependencias que exige que el usuario tenga uno de los roles."""
    allowed = {r.value if isinstance(r, Role) else str(r) for r in roles}

    def _dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed:
            raise PermissionError_(
                "No tiene permisos para realizar esta accion.",
                details={"required": sorted(allowed), "actual": current_user.role},
            )
        return current_user

    return _dependency


def has_role(user: User, *roles: Role) -> bool:
    """Ayudante puro para comprobar el rol de un usuario."""
    allowed = {r.value if isinstance(r, Role) else str(r) for r in roles}
    return user.role in allowed


# Alias de dependencias comunes reutilizables en los routers.
def _lookup_users(session: Session) -> Iterable[User]:  # pragma: no cover - util
    return session.exec(select(User)).all()
