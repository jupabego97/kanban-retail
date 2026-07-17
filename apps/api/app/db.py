"""Configuracion del motor de base de datos y sesiones (SQLModel sincrono)."""
from __future__ import annotations

from typing import Generator

from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.config import settings


def _normalize_database_url(url: str) -> str:
    """Normaliza URLs de Railway/Heroku (postgres:// -> postgresql://)."""
    if url.startswith("postgres://"):
        return "postgresql://" + url[len("postgres://") :]
    return url


def _build_engine():
    """Crea el engine adaptando opciones para SQLite vs PostgreSQL."""
    url = _normalize_database_url(settings.DATABASE_URL)
    connect_args: dict = {}
    kwargs: dict = {"echo": False, "pool_pre_ping": True}

    if url.startswith("sqlite"):
        # SQLite necesita check_same_thread=False para usarse desde FastAPI.
        connect_args["check_same_thread"] = False
        # Para SQLite en memoria se usa un pool estatico y compartido.
        if ":memory:" in url or url == "sqlite://":
            kwargs["poolclass"] = StaticPool
        kwargs.pop("pool_pre_ping", None)

    return create_engine(url, connect_args=connect_args, **kwargs)


engine = _build_engine()


def init_db() -> None:
    """Crea todas las tablas (util para tests o arranque local sin Alembic)."""
    # Importa los modelos para registrarlos en la metadata.
    import app.models  # noqa: F401

    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """Dependencia de FastAPI que entrega una sesion por request."""
    with Session(engine) as session:
        yield session
