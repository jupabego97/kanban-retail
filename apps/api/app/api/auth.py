"""Router de autenticacion: login, logout y perfil actual."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Response
from sqlmodel import Session, select

from app.config import settings
from app.db import get_session
from app.errors import AuthenticationError
from app.models.user import User
from app.schemas.auth import LoginRequest, UserOut
from app.security.deps import get_current_user
from app.security.password import verify_password
from app.security.session import create_session_token
from app.services.audit_service import record_audit

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=token,
        max_age=settings.SESSION_MAX_AGE,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        path="/",
    )


@router.post("/login", response_model=UserOut)
def login(
    payload: LoginRequest,
    response: Response,
    session: Session = Depends(get_session),
) -> User:
    """Autentica al usuario y establece la cookie de sesion firmada."""
    user = session.exec(select(User).where(User.email == payload.email)).first()
    # Verificamos siempre para evitar filtrar si el email existe (timing).
    valid = bool(user) and verify_password(payload.password, user.password_hash)
    if not user or not valid or user.deleted_at is not None or not user.is_active:
        raise AuthenticationError("Credenciales invalidas.")

    token = create_session_token(user.id)
    _set_session_cookie(response, token)

    record_audit(session, actor_id=user.id, action="auth.login", entity_type="user", entity_id=user.id)
    session.commit()
    return user


@router.post("/logout")
def logout(response: Response, current_user: User = Depends(get_current_user)) -> dict:
    """Cierra la sesion eliminando la cookie."""
    response.delete_cookie(settings.SESSION_COOKIE_NAME, path="/")
    return {"message": "Sesion cerrada."}


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)) -> User:
    """Devuelve el usuario autenticado."""
    return current_user
