"""Phase 05 knowledge ingestion use cases; synthetic-only and no publication."""

from __future__ import annotations

import re
from uuid import UUID

from fastapi import UploadFile

from src.core.services.ingestion.upload_validation import UploadRejected, validate_upload_async
from src.core.services.security.security_service import SecurityService
from src.infrastructure.di.inject import inject
from src.infrastructure.providers.storage.quarantine_storage import QuarantineStorage, StorageUnavailable
from src.infrastructure.repositories.ingestion.ingestion_repository import IngestionRepository
from src.infrastructure.security.token_validator import Principal
from src.infrastructure.utils.config_reader import ConfigReader


@inject
class IngestionService:
    def __init__(
        self,
        ingestion_repository: IngestionRepository,
        quarantine_storage: QuarantineStorage,
        security_service: SecurityService,
        config_reader: ConfigReader,
    ):
        self._repo = ingestion_repository
        self._storage = quarantine_storage
        self._security = security_service
        self._settings = config_reader.settings

    def _actor(self, principal: Principal | None) -> tuple[str, str]:
        self._security.authorize(principal, "knowledge:test:ingest")
        if (
            not self._settings.ingestion.enabled
            or self._settings.deployment_zone != "internal"
            or principal is None
            or not principal.subject.startswith("synthetic-")
        ):
            raise PermissionError("Synthetic ingestion unavailable")
        return principal.subject, self._settings.deployment_zone

    async def create_source_async(self, principal: Principal | None, domain: str):
        actor, scope = self._actor(principal)
        if not isinstance(domain, str) or not re.fullmatch(r"[a-z][a-z0-9_-]{1,63}", domain):
            raise UploadRejected("invalid_domain")
        return await self._repo.create_source_async(actor, scope, domain)

    async def get_source_async(self, principal: Principal | None, source_id: UUID):
        actor, scope = self._actor(principal)
        return await self._repo.get_source_owned_async(source_id, actor, scope)

    async def upload_async(
        self, principal: Principal | None, source_id: UUID, file: UploadFile, idempotency_key: str,
    ):
        actor, scope = self._actor(principal)
        if not isinstance(idempotency_key, str) or not re.fullmatch(r"[A-Za-z0-9_-]{8,128}", idempotency_key):
            raise UploadRejected("invalid_idempotency_key")
        name, content, checksum = await validate_upload_async(file, self._settings.ingestion.max_file_bytes)
        job, version, created = await self._repo.stage_async(
            source_id, actor, scope, name, file.content_type, len(content),
            checksum, idempotency_key, self._settings.ingestion.max_attempts,
        )
        if created:
            try:
                await self._storage.put_async(version.object_key, content, checksum)
            except StorageUnavailable:
                await self._repo.fail_staging_async(job.id, actor, scope, "storage_unavailable")
                raise
            if not await self._repo.mark_queued_async(job.id, actor, scope):
                raise UploadRejected("upload_cancelled")
            job.status = "queued"
        return job, version, created

    async def get_job_async(self, principal: Principal | None, job_id: UUID):
        actor, scope = self._actor(principal)
        return await self._repo.get_job_owned_async(job_id, actor, scope)

    async def get_version_async(self, principal: Principal | None, version_id: UUID):
        actor, scope = self._actor(principal)
        return await self._repo.get_version_owned_async(version_id, actor, scope)

    async def cancel_async(self, principal: Principal | None, job_id: UUID) -> bool:
        actor, scope = self._actor(principal)
        return await self._repo.cancel_async(job_id, actor, scope)
