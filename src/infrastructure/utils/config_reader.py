"""Schema-validated deployment configuration without secret interpolation in logs."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from src.infrastructure.di.inject import inject


class ConfigurationError(RuntimeError):
    def __init__(self):
        super().__init__("Invalid application configuration; inspect deployment settings")


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ApiSettings(StrictModel):
    prefix: str = Field(pattern=r"^/[a-z0-9/_-]+$")


class ServerSettings(StrictModel):
    host: str
    port: int = Field(ge=1, le=65535)
    request_timeout_seconds: float = Field(gt=0, le=300)
    max_request_bytes: int = Field(ge=1024, le=10485760)
    rate_limit_per_minute: int = Field(ge=1, le=100000)
    cors_origins: list[str]


class AuthSettings(StrictModel):
    jwks_url: str | None = None
    issuer: str | None = None
    audience: str | None = None
    metrics_permission: str = Field(min_length=1)


class VaultSettings(StrictModel):
    enabled: bool = False
    address: str | None = None
    mount: str = "secret"
    startup_check_path: str | None = None


class DatabaseSettings(StrictModel):
    enabled: bool = False
    url: str | None = None
    vault_secret_path: str | None = None
    tls_mode: Literal["disable", "verify-full"] = "disable"
    tls_ca_file: str | None = None
    pool_size: int = Field(default=5, ge=1, le=100)
    max_overflow: int = Field(default=5, ge=0, le=100)
    pool_timeout_seconds: float = Field(default=10, gt=0, le=120)
    connect_timeout_seconds: float = Field(default=5, gt=0, le=60)
    statement_timeout_ms: int = Field(default=30000, ge=1000, le=300000)


class QdrantSettings(StrictModel):
    enabled: bool = False
    zone: Literal["public", "internal"] | None = None
    url: str | None = None
    api_key: str | None = Field(default=None, repr=False)
    vault_secret_path: str | None = None
    collection_prefix: str = Field(default="scb_vectors", pattern=r"^[a-z][a-z0-9_]{2,39}$")
    schema_version: int = Field(default=1, ge=1, le=100000)
    dimension: int | None = Field(default=None, ge=1, le=65536)
    distance: Literal["Cosine", "Dot", "Euclid"] = "Cosine"
    timeout_seconds: float = Field(default=5, gt=0, le=120)
    max_retries: int = Field(default=2, ge=0, le=3)
    batch_size: int = Field(default=64, ge=1, le=512)


class IngestionSettings(StrictModel):
    enabled: bool = False
    synthetic_only: bool = True
    s3_url: str | None = None
    s3_bucket: str = Field(default="scb-quarantine", pattern=r"^[a-z0-9][a-z0-9.-]{2,62}$")
    s3_access_key: str | None = Field(default=None, repr=False)
    s3_secret_key: str | None = Field(default=None, repr=False)
    clamd_host: str = "127.0.0.1"
    clamd_port: int = Field(default=3310, ge=1, le=65535)
    timeout_seconds: float = Field(default=8, gt=0, le=30)
    max_file_bytes: int = Field(default=1048576, ge=1024, le=5242880)
    lease_seconds: int = Field(default=45, ge=15, le=600)
    max_attempts: int = Field(default=3, ge=1, le=10)


class Settings(StrictModel):
    environment: Literal["development", "integration", "staging", "production"]
    deployment_zone: Literal["public", "internal"]
    api: ApiSettings
    server: ServerSettings
    auth: AuthSettings
    vaulthc: VaultSettings
    database: DatabaseSettings = DatabaseSettings()
    qdrant: QdrantSettings = QdrantSettings()
    ingestion: IngestionSettings = IngestionSettings()

    @model_validator(mode="after")
    def validate_security(self):
        db = self.database
        if db.enabled:
            if bool(db.url) == bool(db.vault_secret_path):
                raise ValueError("Exactly one database credential source is required")
            if db.vault_secret_path and (
                not self.vaulthc.enabled
                or db.vault_secret_path.startswith("/")
                or ".." in db.vault_secret_path.split("/")
            ):
                raise ValueError("Invalid database Vault integration")
            if db.url:
                parts = urlparse(db.url)
                if (
                    parts.scheme != "postgresql+asyncpg"
                    or not parts.hostname
                    or not parts.username
                    or parts.password is None
                    or (self.environment != "development" and parts.password == "")
                    or not parts.path.strip("/")
                    or parts.query
                ):
                    raise ValueError("Invalid database URL")
            if self.environment != "development" and db.tls_mode != "verify-full":
                raise ValueError("Database TLS verification required")
        q = self.qdrant
        if q.enabled:
            if q.zone != self.deployment_zone or not q.dimension:
                raise ValueError("Qdrant scope or schema is incomplete")
            if bool(q.api_key) == bool(q.vault_secret_path):
                raise ValueError("Exactly one Qdrant credential source is required")
            if q.vault_secret_path and (
                not self.vaulthc.enabled
                or q.vault_secret_path.startswith("/")
                or ".." in q.vault_secret_path.split("/")
            ):
                raise ValueError("Invalid Qdrant Vault integration")
            url = urlparse(q.url or "")
            if (
                url.scheme not in {"https", "http"}
                or not url.hostname
                or url.username
                or url.password
                or url.query
                or url.fragment
                or url.path not in {"", "/"}
                or (url.port is not None and not 1 <= url.port <= 65535)
            ):
                raise ValueError("Invalid Qdrant endpoint")
            if url.scheme == "http" and (
                self.environment not in {"development", "integration"} or url.hostname not in {"127.0.0.1", "localhost"}
            ):
                raise ValueError("Qdrant plaintext requires disposable local loopback")
        i = self.ingestion
        if i.enabled:
            if (
                self.environment not in {"development", "integration"}
                or self.deployment_zone != "internal"
                or not i.synthetic_only
                or not db.enabled
                or i.max_file_bytes >= self.server.max_request_bytes
            ):
                raise ValueError("Ingestion restricted to synthetic integration")
            url = urlparse(i.s3_url or "")
            if (
                url.scheme != "http"
                or url.hostname not in {"127.0.0.1", "localhost"}
                or url.username or url.password or url.query or url.fragment
                or url.path not in {"", "/"}
                or not i.s3_access_key or not i.s3_secret_key
                or i.clamd_host not in {"127.0.0.1", "localhost"}
            ):
                raise ValueError("Synthetic ingestion dependencies must use loopback")
        a = self.auth
        values = (a.jwks_url, a.issuer, a.audience)
        if any(values) and not all(values):
            raise ValueError("Identity configuration must be complete")
        if self.environment != "development" and not all(values):
            raise ValueError("Identity configuration required")
        if a.jwks_url:
            parts = urlparse(a.jwks_url)
            if parts.scheme != "https" or not parts.hostname or parts.username or parts.password or parts.fragment:
                raise ValueError("JWKS URL must be an HTTPS endpoint")
        if self.environment != "development":
            if any("example.invalid" in origin for origin in self.server.cors_origins):
                raise ValueError("CORS origins must be configured")
            if self.server.host in ("127.0.0.1", "localhost"):
                raise ValueError("Nondevelopment host must be reachable behind ingress")
            if not self.server.cors_origins or any(
                origin == "*" or not origin.startswith("https://") for origin in self.server.cors_origins
            ):
                raise ValueError("Secure CORS origins required")
        if any(origin == "*" for origin in self.server.cors_origins):
            raise ValueError("Wildcard CORS not permitted")
        if self.vaulthc.enabled:
            parts = urlparse(self.vaulthc.address or "")
            if parts.scheme != "https" or not parts.hostname or not self.vaulthc.startup_check_path:
                raise ValueError("Vault endpoint/check path missing or insecure")
            if not os.environ.get("SCB_VAULT_TOKEN"):
                raise ValueError("Vault token missing")
        return self


@inject
class ConfigReader:
    __di_singleton__ = True

    def __init__(self):
        try:
            environment = os.environ.get("SCB_ENV", "development")
            zone = os.environ.get("SCB_ZONE", "public")
            if environment != "development" and "SCB_ZONE" not in os.environ:
                raise ValueError("Deployment zone must be explicit")
            root = Path(__file__).resolve().parents[2] / "host" / "res"
            filename = "appsettings.development.yaml" if environment == "development" else "appsettings.yaml"
            data = yaml.safe_load((root / filename).read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("Invalid YAML root")
            data["environment"] = environment
            data["deployment_zone"] = zone
            auth = data.setdefault("auth", {})
            for name, field in (("SCB_JWKS_URL", "jwks_url"), ("SCB_ISSUER", "issuer"), ("SCB_AUDIENCE", "audience")):
                if name in os.environ:
                    auth[field] = os.environ[name]
            if "SCB_CORS_ORIGINS" in os.environ:
                import json

                data["server"]["cors_origins"] = json.loads(os.environ["SCB_CORS_ORIGINS"])
            vault = data.setdefault("vaulthc", {})
            enabled = os.environ.get("SCB_VAULT_ENABLED")
            if enabled is not None:
                if enabled.lower() not in {"true", "false"}:
                    raise ValueError("Invalid Vault enable flag")
                vault["enabled"] = enabled.lower() == "true"
            for name, field in (
                ("SCB_VAULT_ADDRESS", "address"),
                ("SCB_VAULT_MOUNT", "mount"),
                ("SCB_VAULT_STARTUP_CHECK_PATH", "startup_check_path"),
            ):
                if name in os.environ:
                    vault[field] = os.environ[name]
            database = data.setdefault("database", {})
            flag = os.environ.get("SCB_DATABASE_ENABLED")
            if flag is not None:
                if flag.lower() not in {"true", "false"}:
                    raise ValueError("Invalid database enable flag")
                database["enabled"] = flag.lower() == "true"
            for name, field in (
                ("SCB_DATABASE_URL", "url"),
                ("SCB_DATABASE_VAULT_PATH", "vault_secret_path"),
                ("SCB_DATABASE_TLS_MODE", "tls_mode"),
                ("SCB_DATABASE_TLS_CA_FILE", "tls_ca_file"),
            ):
                if name in os.environ:
                    database[field] = os.environ[name]
            qdrant = data.setdefault("qdrant", {})
            flag = os.environ.get("SCB_QDRANT_ENABLED")
            if flag is not None:
                if flag.lower() not in {"true", "false"}:
                    raise ValueError("Invalid Qdrant enable flag")
                qdrant["enabled"] = flag.lower() == "true"
            for name, field in (
                ("SCB_QDRANT_ZONE", "zone"),
                ("SCB_QDRANT_URL", "url"),
                ("SCB_QDRANT_API_KEY", "api_key"),
                ("SCB_QDRANT_VAULT_PATH", "vault_secret_path"),
                ("SCB_QDRANT_COLLECTION_PREFIX", "collection_prefix"),
                ("SCB_QDRANT_SCHEMA_VERSION", "schema_version"),
                ("SCB_QDRANT_DIMENSION", "dimension"),
                ("SCB_QDRANT_DISTANCE", "distance"),
                ("SCB_QDRANT_TIMEOUT_SECONDS", "timeout_seconds"),
                ("SCB_QDRANT_MAX_RETRIES", "max_retries"),
                ("SCB_QDRANT_BATCH_SIZE", "batch_size"),
            ):
                if name in os.environ:
                    qdrant[field] = os.environ[name]
            ingestion = data.setdefault("ingestion", {})
            flag = os.environ.get("SCB_INGESTION_ENABLED")
            if flag is not None:
                if flag.lower() not in {"true", "false"}:
                    raise ValueError("Invalid ingestion enable flag")
                ingestion["enabled"] = flag.lower() == "true"
            for name, field in (
                ("SCB_INGESTION_S3_URL", "s3_url"),
                ("SCB_INGESTION_S3_BUCKET", "s3_bucket"),
                ("SCB_INGESTION_S3_ACCESS_KEY", "s3_access_key"),
                ("SCB_INGESTION_S3_SECRET_KEY", "s3_secret_key"),
                ("SCB_INGESTION_CLAMD_HOST", "clamd_host"),
                ("SCB_INGESTION_CLAMD_PORT", "clamd_port"),
                ("SCB_INGESTION_MAX_FILE_BYTES", "max_file_bytes"),
                ("SCB_INGESTION_TIMEOUT_SECONDS", "timeout_seconds"),
                ("SCB_INGESTION_LEASE_SECONDS", "lease_seconds"),
                ("SCB_INGESTION_MAX_ATTEMPTS", "max_attempts"),
            ):
                if name in os.environ:
                    ingestion[field] = os.environ[name]
            self.settings = Settings.model_validate(data)
        except (OSError, ValueError, KeyError, yaml.YAMLError, ValidationError, TypeError):
            raise ConfigurationError() from None

    def get(self, key: str):
        obj = self.settings.model_dump()
        for part in key.split("."):
            obj = obj[part]
        return obj

    def get_api_prefix(self) -> str:
        return self.settings.api.prefix.rstrip("/")
