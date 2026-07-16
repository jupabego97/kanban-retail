"""Esquemas de autenticacion."""
from __future__ import annotations

import re

from pydantic import BaseModel, Field, field_validator

# Validacion de email sencilla que SI acepta dominios de uso interno como .local
# (necesarios para cuentas como admin@tienda.local).
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_email_basic(value: str) -> str:
    value = (value or "").strip().lower()
    if not _EMAIL_RE.match(value):
        raise ValueError("Formato de email invalido.")
    return value


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=1)

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        return validate_email_basic(v)


class UserOut(BaseModel):
    id: int
    email: str
    name: str
    role: str
    is_active: bool

    model_config = {"from_attributes": True}
