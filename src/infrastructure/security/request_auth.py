"""Route-independent authentication boundary with explicit operational allowlist."""

from __future__ import annotations

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from src.infrastructure.security.token_validator import AuthenticationFailed, TokenValidator
from src.infrastructure.utils.config_reader import ConfigReader


class RequestAuthenticationMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, validator: TokenValidator, config: ConfigReader):
        super().__init__(app)
        self.validator = validator
        prefix = config.get_api_prefix()
        self.public_paths = {f"{prefix}/health_check/{name}" for name in ("live", "ready", "startup")}

    async def dispatch(self, request: Request, call_next):
        # Client headers are never an identity source even on public routes.
        forbidden = {"x-user-id", "x-user", "x-role", "x-roles", "x-permissions", "x-principal"}
        if forbidden.intersection(request.headers):
            return JSONResponse({"error": "invalid_identity_context"}, status_code=400)
        if request.url.path in self.public_paths:
            return await call_next(request)
        # Different proxies may select different values from repeated credentials.
        # Reject the ambiguous request rather than trusting a particular occurrence.
        authorization_headers = [
            value for name, value in request.scope.get("headers", []) if name.lower() == b"authorization"
        ]
        if len(authorization_headers) > 1:
            return JSONResponse({"error": "bad_request"}, status_code=400)
        authorization = request.headers.get("authorization", "")
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token or token.strip() != token:
            return JSONResponse({"error": "unauthorized"}, status_code=401, headers={"WWW-Authenticate": "Bearer"})
        try:
            request.state.principal = await self.validator.validate_async(token)
        except AuthenticationFailed:
            return JSONResponse({"error": "unauthorized"}, status_code=401, headers={"WWW-Authenticate": "Bearer"})
        return await call_next(request)
