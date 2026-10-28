"""Business checks and scoped durable ingestion-job workflow (no HTTP endpoints)."""

from __future__ import annotations

import re
from uuid import UUID

from src.infrastructure.di.inject import inject
from src.infrastructure.models.ingestion_job import IngestionJob
from src.infrastructure.repositories.ingestion.ingestion_job_repository import IngestionJobRepository
from src.infrastructure.utils.config_reader import ConfigReader


@inject
class IngestionService:
    def __init__(self, ingestion_job_repository: IngestionJobRepository, config_reader: ConfigReader):
        self._jobs = ingestion_job_repository
        self._zone = config_reader.settings.deployment_zone

    def _scope(self, scope: str) -> str:
        if scope not in {"public", "internal"} or scope != self._zone:
            raise PermissionError("Invalid ingestion deployment scope")
        return scope

    async def enqueue_async(
        self, *, principal: str, scope: str, source_id: UUID, version_id: UUID,
        idempotency_key: str, max_attempts: int = 5
    ) -> IngestionJob:
        self._scope(scope)
        if not isinstance(principal, str) or not principal.strip() or len(principal) > 255:
            raise ValueError("Invalid principal")
        if not isinstance(source_id, UUID) or not isinstance(version_id, UUID):
            raise ValueError("Invalid ingestion identity")
        if not isinstance(idempotency_key, str) or not 1 <= len(idempotency_key) <= 128:
            raise ValueError("Invalid idempotency key")
        if not isinstance(max_attempts, int) or isinstance(max_attempts, bool) or not 1 <= max_attempts <= 20:
            raise ValueError("Invalid retry limit")
        return await self._jobs.enqueue_owned_async(
            principal=principal, scope=scope, source_id=source_id, version_id=version_id,
            idempotency_key=idempotency_key, max_attempts=max_attempts,
        )

    async def claim_next_async(self, *, scope: str, worker_id: str, lease_seconds: int = 60) -> IngestionJob | None:
        self._scope(scope)
        if not isinstance(worker_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", worker_id):
            raise ValueError("Invalid worker identity")
        self._lease(lease_seconds)
        return await self._jobs.claim_next_async(scope=scope, worker_id=worker_id, lease_seconds=lease_seconds)

    @staticmethod
    def _lease(seconds: int) -> None:
        if not isinstance(seconds, int) or isinstance(seconds, bool) or not 5 <= seconds <= 300:
            raise ValueError("Invalid lease duration")

    async def heartbeat_async(
        self, *, scope: str, job_id: UUID, lease_token: UUID, lease_seconds: int = 60
    ) -> bool:
        self._scope(scope)
        self._identity(job_id, lease_token)
        self._lease(lease_seconds)
        return await self._jobs.heartbeat_async(
            job_id=job_id, scope=scope, lease_token=lease_token, lease_seconds=lease_seconds
        )

    async def complete_async(self, *, scope: str, job_id: UUID, lease_token: UUID) -> bool:
        self._scope(scope)
        self._identity(job_id, lease_token)
        return await self._jobs.complete_async(job_id=job_id, scope=scope, lease_token=lease_token)

    async def fail_async(self, *, scope: str, job_id: UUID, lease_token: UUID, error_code: str) -> bool:
        self._scope(scope)
        self._identity(job_id, lease_token)
        if not isinstance(error_code, str) or not re.fullmatch(r"[A-Z][A-Z0-9_]{0,63}", error_code):
            raise ValueError("Invalid structured ingestion error code")
        return await self._jobs.fail_async(
            job_id=job_id, scope=scope, lease_token=lease_token, error_code=error_code
        )

    @staticmethod
    def _identity(job_id: UUID, lease_token: UUID) -> None:
        if not isinstance(job_id, UUID) or not isinstance(lease_token, UUID):
            raise ValueError("Invalid fenced job identity")
