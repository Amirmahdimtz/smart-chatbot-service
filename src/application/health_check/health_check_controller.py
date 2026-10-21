"""Operational endpoints. Metrics are authorization-protected."""
from fastapi import APIRouter, HTTPException, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST

from src.core.services.security.security_service import PermissionDenied, SecurityService
from src.infrastructure.di.inject import inject
from src.infrastructure.security.token_validator import TokenValidator
from src.infrastructure.utils.config_reader import ConfigReader


@inject
class HealthCheckController:
    def __init__(self, security_service: SecurityService, token_validator: TokenValidator,
                 config_reader: ConfigReader):
        self._security = security_service
        self._validator = token_validator
        self._cfg = config_reader

    def api(self) -> APIRouter:
        router = APIRouter(tags=["Health"])

        @router.get("/live", include_in_schema=False)
        async def live_async():
            return {"status": "alive"}

        @router.get("/ready", include_in_schema=False)
        async def ready_async(request: Request):
            if not request.app.state.started or not self._validator.ready:
                raise HTTPException(status_code=503, detail="service_unavailable")
            return {"status": "ready"}

        @router.get("/startup", include_in_schema=False)
        async def startup_async(request: Request):
            if not request.app.state.started:
                raise HTTPException(status_code=503, detail="service_unavailable")
            return {"status": "started"}

        @router.get("/metrics", include_in_schema=False)
        async def metrics_async(request: Request):
            principal = getattr(request.state, "principal", None)
            self._security.authorize(principal, self._cfg.settings.auth.metrics_permission)
            return Response(request.app.state.metrics.output(), media_type=CONTENT_TYPE_LATEST)

        return router
