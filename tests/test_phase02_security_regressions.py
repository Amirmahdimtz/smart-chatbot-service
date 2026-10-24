"""Regression tests for JWKS refresh storms, deadlines, and rate limiter capacity."""

from __future__ import annotations

import asyncio
import base64
import json
from collections import defaultdict, deque
from datetime import UTC, datetime, timedelta

import httpx
import pytest

from src.host.app import create_app
from src.infrastructure.security.http_security import HttpSecurityMiddleware
from src.infrastructure.security.token_validator import AuthenticationFailed, TokenValidator


def _request_scope(client: str = "test-client") -> dict:
    return {"type": "http", "method": "GET", "headers": [], "client": (client, 1234)}


async def _request_events_async(middleware: HttpSecurityMiddleware, client: str) -> list[dict]:
    sent: list[dict] = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        sent.append(message)

    await middleware(_request_scope(client), receive, send)
    return sent


def _statuses(messages: list[dict]) -> list[int]:
    return [message["status"] for message in messages if message["type"] == "http.response.start"]


def test_expired_ip_buckets_removed_before_capacity_limit():
    async def app(scope, receive, send):
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})

    async def exercise():
        guard = HttpSecurityMiddleware(app, max_bytes=1048576, rate_per_minute=1, timeout=1)
        guard._hits = defaultdict(deque, {f"old-{i}": deque([-1000.0]) for i in range(10000)})
        assert _statuses(await _request_events_async(guard, "new-client")) == [200]
        assert len(guard._hits) == 1
        assert _statuses(await _request_events_async(guard, "new-client")) == [429]

    asyncio.run(exercise())


def test_timeouts_before_and_after_headers_respect_asgi_response_lifecycle():
    async def exercise(headers_already_sent: bool):
        async def slow_app(scope, receive, send):
            if headers_already_sent:
                await send({"type": "http.response.start", "status": 200, "headers": []})
            await asyncio.sleep(0.15)

        guard = HttpSecurityMiddleware(slow_app, max_bytes=1048576, rate_per_minute=10, timeout=0.01)
        if headers_already_sent:
            sent: list[dict] = []

            async def receive():
                return {"type": "http.request", "body": b"", "more_body": False}

            async def send(message):
                sent.append(message)

            with pytest.raises(TimeoutError):
                await guard(_request_scope(), receive, send)
            assert _statuses(sent) == [200]
        else:
            assert _statuses(await _request_events_async(guard, "new-client")) == [504]

    asyncio.run(exercise(False))
    asyncio.run(exercise(True))


def _configured_validator(monkeypatch) -> TokenValidator:
    monkeypatch.setenv("SCB_ENV", "development")
    monkeypatch.setenv("SCB_ZONE", "public")
    monkeypatch.setenv("SCB_JWKS_URL", "https://issuer.example.test/jwks")
    monkeypatch.setenv("SCB_ISSUER", "https://issuer.example.test/")
    monkeypatch.setenv("SCB_AUDIENCE", "scb-public")
    return create_app().state.container.resolve(TokenValidator)


def _unknown_key_token(token: str) -> str:
    _, payload, signature = token.split(".")
    header = (
        base64.urlsafe_b64encode(json.dumps({"alg": "RS256", "typ": "JWT", "kid": "untrusted-key"}).encode())
        .rstrip(b"=")
        .decode()
    )
    return ".".join((header, payload, signature))


@pytest.fixture
def identity():
    import jwt
    from cryptography.hazmat.primitives.asymmetric import rsa

    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public = private.public_key().public_numbers()

    def encode(number):
        return base64.urlsafe_b64encode(number.to_bytes((number.bit_length() + 7) // 8, "big")).rstrip(b"=").decode()

    jwks = {
        "keys": [
            {
                "kty": "RSA",
                "use": "sig",
                "alg": "RS256",
                "kid": "test-key",
                "n": encode(public.n),
                "e": encode(public.e),
            }
        ]
    }

    def token():
        now = datetime.now(UTC)
        return jwt.encode(
            {
                "iss": "https://issuer.example.test/",
                "aud": "scb-public",
                "sub": "test-subject",
                "iat": now,
                "nbf": now,
                "exp": now + timedelta(minutes=2),
            },
            private,
            algorithm="RS256",
            headers={"kid": "test-key"},
        )

    return jwks, token


def test_jwks_unknown_kid_burst_does_not_trigger_refresh_storm_and_idle_refreshes(identity, monkeypatch):
    validator = _configured_validator(monkeypatch)
    total_requests = 0

    async def keys(request):
        nonlocal total_requests
        total_requests += 1
        return httpx.Response(200, json=identity[0])

    async def exercise():
        await validator._client.aclose()
        validator._client = httpx.AsyncClient(transport=httpx.MockTransport(keys))
        validator._refresh_interval_seconds = 0.02
        try:
            await validator.refresh_async()
            unknown = _unknown_key_token(identity[1]())

            async def invalid_request():
                with pytest.raises(AuthenticationFailed):
                    await validator.validate_async(unknown)

            await asyncio.gather(*(invalid_request() for _ in range(25)))
            assert total_requests == 1
            validator._last_refresh_attempt = float("-inf")
            await asyncio.gather(*(invalid_request() for _ in range(25)))
            assert total_requests == 2
            validator._retry_interval_seconds = 0.005
            await validator.start_async()
            await asyncio.sleep(0.09)
            assert total_requests >= 3
            assert validator.ready
        finally:
            await validator.close_async()
        assert validator._refresh_task is None

    asyncio.run(exercise())


def test_jwks_outage_after_ttl_fails_closed(identity, monkeypatch):
    validator = _configured_validator(monkeypatch)

    async def available(request):
        return httpx.Response(200, json=identity[0])

    async def offline(request):
        return httpx.Response(503)

    async def exercise():
        await validator._client.aclose()
        validator._client = httpx.AsyncClient(transport=httpx.MockTransport(available))
        try:
            await validator.refresh_async()
            assert validator.ready
            validator._last_refresh = datetime.now(UTC) - validator._ttl - timedelta(seconds=1)
            assert not validator.ready
            await validator._client.aclose()
            validator._client = httpx.AsyncClient(transport=httpx.MockTransport(offline))
            validator._last_refresh_attempt = float("-inf")
            with pytest.raises(AuthenticationFailed):
                await validator.validate_async(identity[1]())
            assert not validator.ready
        finally:
            await validator.close_async()

    asyncio.run(exercise())


def test_validator_reinitializes_jwks_client_and_cache_across_app_lifespans(monkeypatch, identity):
    """A second lifespan must refresh JWKS, not reuse a closed client or stale readiness."""
    from fastapi.testclient import TestClient

    monkeypatch.setenv("SCB_ENV", "development")
    monkeypatch.setenv("SCB_ZONE", "public")
    monkeypatch.setenv("SCB_JWKS_URL", "https://issuer.example.test/jwks")
    monkeypatch.setenv("SCB_ISSUER", "https://issuer.example.test/")
    monkeypatch.setenv("SCB_AUDIENCE", "scb-public")

    client_type = httpx.AsyncClient
    calls = 0

    async def jwks_response(request):
        nonlocal calls
        calls += 1
        return httpx.Response(200, json=identity[0])

    def client_factory(*args, **kwargs):
        return client_type(transport=httpx.MockTransport(jwks_response))

    monkeypatch.setattr("src.infrastructure.security.token_validator.httpx.AsyncClient", client_factory)
    app = create_app()
    validator = app.state.container.resolve(TokenValidator)

    for expected_calls in (1, 2):
        with TestClient(app) as client:
            assert validator.ready
            assert not validator._client.is_closed
            assert client.get("/api/v1/health_check/ready").status_code == 200
            assert calls == expected_calls
        assert validator._client.is_closed
        assert not validator.ready
