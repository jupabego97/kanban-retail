"""Configuracion central de la aplicacion basada en variables de entorno."""
from __future__ import annotations

from functools import lru_cache
from typing import List, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Ajustes cargados desde el entorno o el archivo .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Base de datos. Se acepta SQLite para tests/dev y PostgreSQL para produccion.
    DATABASE_URL: str = "sqlite:///./dev.db"

    # Seguridad
    SECRET_KEY: str = "dev-secret-key-cambiar-en-produccion"
    ENVIRONMENT: str = "development"

    # Cookies de sesion
    COOKIE_SECURE: bool = False
    SESSION_MAX_AGE: int = 28800  # 8 horas
    SESSION_COOKIE_NAME: str = "kanban_session"

    # CORS: aceptar string CSV o lista JSON. Se normaliza a List[str].
    CORS_ORIGINS: Union[str, List[str]] = "http://localhost:3000"

    # Rate limiting (en memoria, suficiente para v1)
    RATE_LIMIT_MAX_REQUESTS: int = 300
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> List[str]:
        """Permite CORS_ORIGINS como CSV o lista."""
        if value is None:
            return []
        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                return []
            if raw.startswith("["):
                import json

                parsed = json.loads(raw)
                return [str(origin).strip() for origin in parsed if str(origin).strip()]
            return [origin.strip() for origin in raw.split(",") if origin.strip()]
        if isinstance(value, (list, tuple)):
            return [str(origin).strip() for origin in value if str(origin).strip()]
        return []

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    """Devuelve una instancia cacheada de la configuracion."""
    return Settings()


settings = get_settings()
