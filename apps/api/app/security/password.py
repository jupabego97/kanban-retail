"""Hashing y verificacion de contrasenas con Argon2."""
from __future__ import annotations

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHash, VerifyMismatchError

# Instancia reutilizable con parametros por defecto (seguros para v1).
_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """Devuelve el hash Argon2 de la contrasena."""
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verifica la contrasena contra su hash. Nunca levanta si no coincide."""
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, InvalidHash, Exception):  # noqa: BLE001
        return False


def needs_rehash(password_hash: str) -> bool:
    """Indica si el hash deberia recalcularse (parametros obsoletos)."""
    try:
        return _hasher.check_needs_rehash(password_hash)
    except Exception:  # noqa: BLE001
        return False
