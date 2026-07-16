"""Punto de entrada de la aplicacion FastAPI."""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.api import (
    audit,
    auth,
    demands,
    health,
    imports,
    metrics,
    products,
    suppliers,
    users,
)
from app.config import settings
from app.errors import DomainError
from app.logging_setup import get_logger, setup_logging
from app.middleware import RateLimitMiddleware, SecurityHeadersMiddleware

setup_logging(logging.INFO)
logger = get_logger("app")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Kanban Retail - Captura de Demanda API",
        version=__version__,
        description="API para gestionar la demanda insatisfecha de una tienda (single-tenant).",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Cabeceras de seguridad y rate limiting.
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        RateLimitMiddleware,
        max_requests=settings.RATE_LIMIT_MAX_REQUESTS,
        window_seconds=settings.RATE_LIMIT_WINDOW_SECONDS,
    )

    _register_exception_handlers(app)
    _register_routers(app)
    return app


def _register_routers(app: FastAPI) -> None:
    prefix = "/api"
    app.include_router(health.router, prefix=prefix)
    app.include_router(auth.router, prefix=prefix)
    app.include_router(users.router, prefix=prefix)
    app.include_router(suppliers.router, prefix=prefix)
    app.include_router(products.router, prefix=prefix)
    app.include_router(demands.router, prefix=prefix)
    app.include_router(imports.router, prefix=prefix)
    app.include_router(metrics.router, prefix=prefix)
    app.include_router(audit.router, prefix=prefix)


def _register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def _domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
        # Nunca exponemos SQL crudo: solo el payload controlado del dominio.
        return JSONResponse(status_code=exc.status_code, content=exc.to_dict())

    @app.exception_handler(RequestValidationError)
    async def _validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"code": "validation_error", "message": "Datos invalidos.", "details": jsonable_encoder(exc.errors())},
        )

    @app.exception_handler(Exception)
    async def _unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
        # Registramos el detalle pero devolvemos un mensaje generico al cliente.
        logger.exception("Error no controlado", extra={"path": str(request.url.path)})
        return JSONResponse(
            status_code=500,
            content={"code": "internal_error", "message": "Ocurrio un error interno."},
        )


app = create_app()


@app.get("/")
def root() -> dict:
    return {"service": "kanban-retail-api", "version": __version__, "docs": "/docs"}
