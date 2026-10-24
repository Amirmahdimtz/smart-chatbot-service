"""Application factory and lifespan; no import-time network or config side effects."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.application.web import mount_controllers
from src.core.services.security.security_service import PermissionDenied
from src.infrastructure.context.vault.vault_service import VaultService
from src.infrastructure.di.bootstrap import bootstrap_di
from src.infrastructure.observability.telemetry import HttpMetrics, SafeJsonFormatter, TelemetryMiddleware
from src.infrastructure.security.http_security import HttpSecurityMiddleware
from src.infrastructure.security.request_auth import RequestAuthenticationMiddleware
from src.infrastructure.security.token_validator import TokenValidator
from src.infrastructure.utils.config_reader import ConfigReader


def create_app() -> FastAPI:
    container = bootstrap_di()
    config = container.resolve(ConfigReader)
    settings = config.settings
    validator = container.resolve(TokenValidator)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.started = False
        try:
            await validator.open_async()
            if settings.vaulthc.enabled:
                await container.resolve(VaultService).check_async()
            if settings.auth.jwks_url:
                await validator.refresh_async()
            if settings.environment != "development" and not validator.ready:
                raise RuntimeError("Identity service unavailable during startup")
            await validator.start_async()
            app.state.started = True
            yield
        finally:
            app.state.started = False
            await validator.close_async()

    app = FastAPI(
        title="Smart Chatbot Service",
        version="0.2.0",
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.state.metrics = HttpMetrics()
    app.state.started = False
    app.state.container = container

    @app.exception_handler(PermissionDenied)
    async def permission_denied(request: Request, exc: PermissionDenied):
        return JSONResponse({"error": "forbidden"}, status_code=403)

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException):
        if exc.status_code == 503:
            return JSONResponse({"error": "service_unavailable"}, status_code=503)
        return JSONResponse({"error": "request_failed"}, status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request: Request, exc: RequestValidationError):
        return JSONResponse({"error": "invalid_request"}, status_code=422)

    @app.exception_handler(Exception)
    async def unhandled(request: Request, exc: Exception):
        return JSONResponse({"error": "internal_error"}, status_code=500)

    mount_controllers(app, container)
    app.add_middleware(RequestAuthenticationMiddleware, validator=validator, config=config)
    app.add_middleware(TelemetryMiddleware, metrics=app.state.metrics)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.server.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-Correlation-ID"],
    )
    app.add_middleware(
        HttpSecurityMiddleware,
        max_bytes=settings.server.max_request_bytes,
        rate_per_minute=settings.server.rate_limit_per_minute,
        timeout=settings.server.request_timeout_seconds,
    )
    logger = logging.getLogger("scb.http")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(SafeJsonFormatter())
        logger.addHandler(handler)
    logger.propagate = False
    return app


app = create_app()
