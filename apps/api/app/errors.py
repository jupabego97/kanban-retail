"""Errores de dominio con codigos estables.

Cada error expone un `code` estable (para clientes) y un `status_code` HTTP.
Nunca se exponen mensajes crudos de SQL: los handlers de FastAPI convierten
estas excepciones en respuestas JSON controladas.
"""
from __future__ import annotations

from typing import Any, Optional


class DomainError(Exception):
    """Error base del dominio."""

    code: str = "domain_error"
    status_code: int = 400

    def __init__(self, message: str, *, details: Optional[Any] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details

    def to_dict(self) -> dict:
        payload: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.details is not None:
            payload["details"] = self.details
        return payload


class NotFoundError(DomainError):
    code = "not_found"
    status_code = 404


class ValidationError(DomainError):
    code = "validation_error"
    status_code = 422


class ConflictError(DomainError):
    code = "conflict"
    status_code = 409


class VersionConflictError(ConflictError):
    """Se levanta cuando la version optimista no coincide (edicion concurrente)."""

    code = "version_conflict"
    status_code = 409


class InvalidTransitionError(DomainError):
    """Transicion de estado no permitida por la maquina de estados."""

    code = "invalid_transition"
    status_code = 409


class AuthenticationError(DomainError):
    code = "authentication_error"
    status_code = 401


class PermissionError_(DomainError):
    """Error de autorizacion (rol insuficiente)."""

    code = "forbidden"
    status_code = 403


class DuplicateError(ConflictError):
    code = "duplicate"
    status_code = 409
