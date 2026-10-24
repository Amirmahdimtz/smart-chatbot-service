"""Real ASGI request/lifespan and security negative tests (keys exist only in tests)."""

from __future__ import annotations

import base64
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from src.host.app import create_app
from src.infrastructure.di.bootstrap import bootstrap_di
from src.infrastructure.security.token_validator import TokenValidator
from src.infrastructure.utils.config_reader import ConfigReader, ConfigurationError


@pytest.fixture
def identity():
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public = private.public_key().public_numbers()

    def encode(n):
        return base64.urlsafe_b64encode(n.to_bytes((n.bit_length() + 7) // 8, "big")).rstrip(b"=").decode()

    jwks = {
        "keys": [
            {"kty": "RSA", "use": "sig", "alg": "RS256", "kid": "key-a", "n": encode(public.n), "e": encode(public.e)}
        ]
    }

    def token(**changes):
        now = datetime.now(UTC)
        claims = {
            "iss": "https://issuer.example.test/",
            "aud": "scb-public",
            "sub": "test-subject",
            "iat": now,
            "nbf": now,
            "exp": now + timedelta(minutes=2),
            "permissions": [],
        }
        claims.update(changes)
        return jwt.encode(claims, private, algorithm="RS256", headers={"kid": "key-a"})

    return jwks, token


@pytest.fixture
def client(identity, monkeypatch):
    monkeypatch.setenv("SCB_ENV", "development")
    monkeypatch.setenv("SCB_ZONE", "public")
    monkeypatch.setenv("SCB_JWKS_URL", "https://issuer.example.test/jwks")
    monkeypatch.setenv("SCB_ISSUER", "https://issuer.example.test/")
    monkeypatch.setenv("SCB_AUDIENCE", "scb-public")
    app = create_app()
    validator = app.state.container.resolve(TokenValidator)

    async def keys(request):
        return httpx.Response(200, json=identity[0])

    validator._client = httpx.AsyncClient(transport=httpx.MockTransport(keys))
    with TestClient(app) as test_client:
        yield test_client, identity[1], app


def test_discovery_is_deterministic_and_singletons_are_per_app(monkeypatch):
    monkeypatch.delenv("SCB_JWKS_URL", raising=False)
    monkeypatch.delenv("SCB_ISSUER", raising=False)
    monkeypatch.delenv("SCB_AUDIENCE", raising=False)
    a = create_app()
    b = create_app()
    paths = {
        "/api/v1/health_check/live": 200,
        "/api/v1/health_check/startup": 200,
        "/api/v1/health_check/ready": 503,
        "/api/v1/health_check/metrics": 401,
    }
    with TestClient(a) as left, TestClient(b) as right:
        assert {path: left.get(path).status_code for path in paths} == paths
        assert {path: right.get(path).status_code for path in paths} == paths
    assert a.state.container.resolve(ConfigReader) is a.state.container.resolve(ConfigReader)
    assert a.state.container.resolve(ConfigReader) is not b.state.container.resolve(ConfigReader)
    container = bootstrap_di()
    assert len(container._providers) == 5


def test_health_and_telemetry(client):
    http, _, app = client
    rid = str(uuid4())
    r = http.get("/api/v1/health_check/live", headers={"x-request-id": rid, "x-correlation-id": "bad"})
    assert r.status_code == 200
    assert r.json() == {"status": "alive"}
    assert r.headers["X-Request-ID"] == rid
    assert r.headers["X-Correlation-ID"] != "bad"
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert http.get("/api/v1/health_check/ready").status_code == 200
    assert http.get("/api/v1/health_check/startup").status_code == 200
    assert b"http_requests_total" in app.state.metrics.output()


def test_401_403_and_valid_authorization(client):
    http, token, _ = client
    url = "/api/v1/health_check/metrics"
    assert http.get(url).status_code == 401
    assert http.get(url, headers={"Authorization": "Bearer garbage"}).status_code == 401
    assert http.get(url, headers={"Authorization": "Bearer " + token()}).status_code == 403
    res = http.get(url, headers={"Authorization": "Bearer " + token(permissions=["observability:read"])})
    assert res.status_code == 200
    assert "http_requests_total" in res.text


def test_token_tampering_wrong_audience_expired_future_nbf(client):
    http, token, _ = client
    url = "/api/v1/health_check/metrics"

    def check(t):
        assert http.get(url, headers={"Authorization": "Bearer " + t}).status_code == 401

    good = token(permissions=["observability:read"])
    signed, body, sig = good.split(".")
    tampered = base64.urlsafe_b64encode(b'{"sub":"intruder"}').rstrip(b"=").decode()
    check(".".join((signed, tampered, sig)))
    check(token(aud="scb-internal"))
    check(token(aud=["scb-public", "scb-internal"]))
    check(token(exp=datetime.now(UTC) - timedelta(minutes=1)))
    check(token(nbf=datetime.now(UTC) + timedelta(minutes=5)))
    check(token(sub=""))
    check(token(permissions="observability:read"))
    assert (
        http.get(url, headers={"Authorization": "Bearer " + token(roles=["admin"], permissions=[])}).status_code == 403
    )


def test_cross_zone_isolation_by_dedicated_audience(client):
    http, token, _ = client
    assert (
        http.get(
            "/api/v1/health_check/metrics",
            headers={"Authorization": "Bearer " + token(aud="scb-internal", permissions=["observability:read"])},
        ).status_code
        == 401
    )


def test_identity_header_spoofing_and_options(client):
    http, token, _ = client
    r = http.get("/api/v1/health_check/live", headers={"x-user-id": "staff"})
    assert r.status_code == 400
    assert (
        http.get(
            "/api/v1/health_check/metrics",
            headers={"x-role": "admin", "Authorization": "Bearer " + token(permissions=["observability:read"])},
        ).status_code
        == 400
    )
    r = http.options(
        "/api/v1/health_check/live",
        headers={"Origin": "https://attacker.invalid", "Access-Control-Request-Method": "GET"},
    )
    assert "access-control-allow-origin" not in r.headers


def test_request_size_and_malformed_length(client):
    http, _, _ = client
    url = "/api/v1/health_check/live"
    assert http.get(url, headers={"content-length": "xyz"}).status_code == 400
    assert http.get(url, headers={"content-length": "999999999"}).status_code == 413


def test_production_fails_closed_without_idp_and_zone(monkeypatch):
    monkeypatch.setenv("SCB_ENV", "production")
    for name in ("SCB_ZONE", "SCB_JWKS_URL", "SCB_ISSUER", "SCB_AUDIENCE", "SCB_CORS_ORIGINS"):
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(ConfigurationError):
        create_app()
    monkeypatch.setenv("SCB_ZONE", "public")
    with pytest.raises(ConfigurationError):
        create_app()


def test_invalid_config_redacted(monkeypatch):
    monkeypatch.setenv("SCB_ENV", "bogus")
    monkeypatch.setenv("SCB_AUDIENCE", "test-credential-do-not-print")
    with pytest.raises(ConfigurationError) as exc:
        create_app()
    assert "test-credential" not in str(exc.value)


def test_development_without_idp_is_not_ready(monkeypatch):
    monkeypatch.setenv("SCB_ENV", "development")
    for name in ("SCB_JWKS_URL", "SCB_ISSUER", "SCB_AUDIENCE"):
        monkeypatch.delenv(name, raising=False)
    with TestClient(create_app()) as http:
        assert http.get("/api/v1/health_check/live").status_code == 200
        assert http.get("/api/v1/health_check/ready").status_code == 503
        assert http.get("/api/v1/health_check/metrics").status_code == 401


def test_vault_configuration_fails_closed(monkeypatch):
    monkeypatch.setenv("SCB_ENV", "development")
    monkeypatch.setenv("SCB_VAULT_ENABLED", "invalid")
    with pytest.raises(ConfigurationError):
        create_app()

    monkeypatch.setenv("SCB_VAULT_ENABLED", "true")
    monkeypatch.setenv("SCB_VAULT_ADDRESS", "http://vault.example.invalid")
    monkeypatch.setenv("SCB_VAULT_STARTUP_CHECK_PATH", "health")
    monkeypatch.setenv("SCB_VAULT_TOKEN", "test")
    with pytest.raises(ConfigurationError):
        create_app()

    monkeypatch.setenv("SCB_VAULT_ADDRESS", "https://vault.example.invalid")
    monkeypatch.delenv("SCB_VAULT_TOKEN", raising=False)
    with pytest.raises(ConfigurationError):
        create_app()


def test_duplicate_authorization_headers_are_rejected(client):
    http, token, _ = client
    auth = "Bearer " + token(permissions=["observability:read"])
    response = http.get(
        "/api/v1/health_check/metrics",
        headers=[("Authorization", auth), ("Authorization", "Bearer invalid")],
    )
    assert response.status_code == 400
