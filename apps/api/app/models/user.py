"""Modelo de usuario del sistema."""
from __future__ import annotations

from typing import Optional

from sqlmodel import Field

from app.enums import Role
from app.models.base import TimestampMixin


class User(TimestampMixin, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True, nullable=False)
    name: str = Field(nullable=False)
    password_hash: str = Field(nullable=False)
    # El rol se guarda como texto (ver app/enums.py) para portabilidad.
    role: str = Field(default=Role.OPERATOR.value, index=True, nullable=False)
    is_active: bool = Field(default=True, nullable=False)
