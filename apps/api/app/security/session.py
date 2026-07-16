"""Gestion de tokens de sesion firmados con itsdangerous."""
from __future__ import annotations

from typing import Optional

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.config import settings

_SALT = "kanban-session-v1"


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(settings.SECRET_KEY, salt=_SALT)


def create_session_token(user_id: int) -> str:
    """Crea un token firmado que contiene el id del usuario."""
    return _serializer().dumps({"uid": user_id})


def read_session_token(token: str, max_age: Optional[int] = None) -> Optional[int]:
    """Valida y decodifica el token; devuelve el user_id o None si es invalido."""
    if not token:
        return None
    max_age = settings.SESSION_MAX_AGE if max_age is None else max_age
    try:
        data = _serializer().loads(token, max_age=max_age)
    except (BadSignature, SignatureExpired, Exception):  # noqa: BLE001
        return None
    if not isinstance(data, dict):
        return None
    uid = data.get("uid")
    return int(uid) if isinstance(uid, int) else None
