"""OIDC/JWKS signature verification. No user-provided unsigned identity is trusted."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import httpx
import jwt
from jwt import InvalidTokenError, PyJWKSet

from src.infrastructure.di.inject import inject
from src.infrastructure.utils.config_reader import ConfigReader


class AuthenticationFailed(RuntimeError):
    pass


@dataclass(frozen=True)
class Principal:
    subject: str
    issuer: str
    audience: str
    roles: frozenset[str]
    permissions: frozenset[str]


@inject
class TokenValidator:
    __di_singleton__ = True

    def __init__(self, config_reader: ConfigReader):
        self._cfg = config_reader.settings.auth
        self._client = httpx.AsyncClient(timeout=5.0, follow_redirects=False, trust_env=False)
        self._keys: dict[str, object] = {}
        self._refresh_lock = asyncio.Lock()
        self._last_refresh: datetime | None = None
        self._ttl = timedelta(minutes=5)
        self._refresh_interval_seconds = 60.0
        self._retry_interval_seconds = 15.0
        self._last_refresh_attempt = float("-inf")
        self._refresh_task: asyncio.Task[None] | None = None

    @property
    def ready(self) -> bool:
        return bool(self._keys and self._last_refresh and datetime.now(UTC) - self._last_refresh <= self._ttl)

    async def refresh_async(self) -> None:
        """Bound refresh attempts across all callers, including untrusted unknown key IDs."""
        if not self._cfg.jwks_url:
            raise AuthenticationFailed("Identity service is not configured")
        async with self._refresh_lock:
            now = time.monotonic()
            if now - self._last_refresh_attempt < self._retry_interval_seconds:
                if not self.ready:
                    raise AuthenticationFailed("Identity keys are unavailable")
                return
            self._last_refresh_attempt = now
            try:
                response = await self._client.get(self._cfg.jwks_url)
                response.raise_for_status()
                body = response.json()
                jwk_set = PyJWKSet.from_dict(body)
                keys = {}
                for jwk in jwk_set.keys:
                    if (
                        jwk.key_type == "RSA"
                        and jwk.algorithm_name == "RS256"
                        and jwk.public_key_use in (None, "sig")
                        and jwk.key_id
                    ):
                        if jwk.key_id in keys:
                            raise ValueError("Duplicate key id")
                        keys[jwk.key_id] = jwk.key
                if not keys:
                    raise ValueError("No acceptable verification keys")
                self._keys = keys
                self._last_refresh = datetime.now(UTC)
            except (httpx.HTTPError, ValueError, TypeError, KeyError, jwt.PyJWTError):
                # Preserve last known good keys for short network faults; never accept unknown keys.
                raise AuthenticationFailed("Identity keys are unavailable") from None

    async def start_async(self) -> None:
        """Refresh the signing-key cache even when there are no authenticated requests."""
        if self._cfg.jwks_url and (self._refresh_task is None or self._refresh_task.done()):
            self._refresh_task = asyncio.create_task(self._refresh_loop_async())

    async def _refresh_loop_async(self) -> None:
        while True:
            await asyncio.sleep(self._refresh_interval_seconds)
            try:
                await self.refresh_async()
            except AuthenticationFailed:
                # Preserve trusted keys only for their configured bounded TTL.
                continue

    async def validate_async(self, token: str) -> Principal:
        if not token or len(token) > 8192 or not self._cfg.jwks_url:
            raise AuthenticationFailed("Invalid credentials")
        try:
            header = jwt.get_unverified_header(token)
            if header.get("alg") != "RS256" or not isinstance(header.get("kid"), str):
                raise AuthenticationFailed("Invalid credentials")
            if not self.ready:
                await self.refresh_async()
            key = self._keys.get(header["kid"])
            if key is None:
                await self.refresh_async()
                key = self._keys.get(header["kid"])
            if key is None:
                raise AuthenticationFailed("Invalid credentials")
            claims = jwt.decode(
                token,
                key=key,
                algorithms=["RS256"],
                issuer=self._cfg.issuer,
                audience=self._cfg.audience,
                leeway=0,
                options={"require": ["sub", "iss", "aud", "exp", "iat", "nbf"]},
            )
            if claims.get("aud") != self._cfg.audience:
                raise AuthenticationFailed("Invalid credentials")
            subject = claims["sub"]
            if not isinstance(subject, str) or not subject or len(subject) > 256:
                raise AuthenticationFailed("Invalid credentials")

            def names(field):
                value = claims.get(field, [])
                if (
                    not isinstance(value, list)
                    or len(value) > 100
                    or any(not isinstance(x, str) or not x or len(x) > 128 for x in value)
                ):
                    raise AuthenticationFailed("Invalid credentials")
                return frozenset(value)

            return Principal(subject, claims["iss"], self._cfg.audience, names("roles"), names("permissions"))
        except (InvalidTokenError, ValueError, KeyError, TypeError, AuthenticationFailed):
            raise AuthenticationFailed("Invalid credentials") from None

    async def close_async(self) -> None:
        if self._refresh_task is not None:
            self._refresh_task.cancel()
            try:
                await self._refresh_task
            except asyncio.CancelledError:
                pass
            self._refresh_task = None
        await self._client.aclose()
