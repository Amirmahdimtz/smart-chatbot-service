"""Scoped PostgreSQL queue operations with skip-locked claims and lease fencing."""

from __future__ import annotations

from datetime import timedelta
from uuid import UUID, uuid4

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from src.infrastructure.context.sql_db.psql_dbcontext import PsqlDbContext
from src.infrastructure.di.inject import inject
from src.infrastructure.models.entities import DocumentVersion, KnowledgeDocument, KnowledgeSource
from src.infrastructure.models.ingestion_job import IngestionJob
from src.infrastructure.repositories.base.base_repository import BaseRepository


@inject
class IngestionJobRepository(BaseRepository[IngestionJob]):
    def __init__(self, db_context: PsqlDbContext):
        super().__init__(db_context=db_context, model=IngestionJob)

    async def insert_async(self, entity, *, session=None):
        raise PermissionError("Use scoped ingestion enqueue")

    async def insert_and_get_id_async(self, entity, *, session=None):
        raise PermissionError("Use scoped ingestion enqueue")

    async def get_by_id_async(self, entity_id, *, session=None):
        raise PermissionError("Ingestion job scope is required")

    async def get_all_async(self, *, session=None):
        raise PermissionError("Ingestion job scope is required")

    async def update_async(self, entity, *, session=None):
        raise PermissionError("Use fenced ingestion transitions")

    async def delete_async(self, entity_id, *, session=None):
        raise PermissionError("Ingestion jobs cannot be removed through generic CRUD")

    async def enqueue_owned_async(
        self, *, principal: str, scope: str, source_id: UUID, version_id: UUID, idempotency_key: str, max_attempts: int
    ) -> IngestionJob:
        async with self._db.transaction_async() as session:
            allowed = await session.scalar(
                select(DocumentVersion.id)
                .join(
                    KnowledgeDocument,
                    and_(
                        KnowledgeDocument.id == DocumentVersion.document_id,
                        KnowledgeDocument.deployment_scope == DocumentVersion.deployment_scope,
                    ),
                )
                .join(
                    KnowledgeSource,
                    and_(
                        KnowledgeSource.id == KnowledgeDocument.source_id,
                        KnowledgeSource.deployment_scope == KnowledgeDocument.deployment_scope,
                    ),
                )
                .where(
                    DocumentVersion.id == version_id,
                    DocumentVersion.deployment_scope == scope,
                    DocumentVersion.state == "draft",
                    KnowledgeSource.id == source_id,
                    KnowledgeSource.owner_principal_id == principal,
                    KnowledgeSource.deployment_scope == scope,
                )
            )
            if allowed is None:
                raise PermissionError("Source or draft version unavailable")
            inserted = await session.scalar(
                pg_insert(IngestionJob)
                .values(
                    id=uuid4(),
                    source_id=source_id,
                    document_version_id=version_id,
                    deployment_scope=scope,
                    idempotency_key=idempotency_key,
                    max_attempts=max_attempts,
                    status="queued",
                )
                .on_conflict_do_nothing(constraint="uq_ingestion_source_idempotency")
                .returning(IngestionJob.id)
            )
            job = await session.scalar(
                select(IngestionJob).where(
                    IngestionJob.id == inserted if inserted is not None else IngestionJob.source_id == source_id,
                    *(() if inserted is not None else (IngestionJob.idempotency_key == idempotency_key,)),
                )
            )
            if job is None:
                raise RuntimeError("Ingestion enqueue could not be verified")
            if (
                job.document_version_id != version_id
                or job.deployment_scope != scope
                or job.max_attempts != max_attempts
            ):
                raise ValueError("Idempotency key reused with different job parameters")
            return job

    async def claim_next_async(self, *, scope: str, worker_id: str, lease_seconds: int) -> IngestionJob | None:
        async with self._db.transaction_async() as session:
            now = await session.scalar(select(func.now()))
            await session.execute(
                update(IngestionJob)
                .where(
                    IngestionJob.deployment_scope == scope,
                    IngestionJob.status == "processing",
                    IngestionJob.lease_expires_at <= now,
                    IngestionJob.attempts >= IngestionJob.max_attempts,
                )
                .values(
                    status="dead_letter",
                    error_code="LEASE_EXHAUSTED",
                    lease_owner=None,
                    lease_token=None,
                    lease_expires_at=None,
                    updated_at=now,
                )
            )
            job = await session.scalar(
                select(IngestionJob)
                .where(
                    IngestionJob.deployment_scope == scope,
                    IngestionJob.attempts < IngestionJob.max_attempts,
                    or_(
                        and_(IngestionJob.status.in_(("queued", "retry_wait")), IngestionJob.available_at <= now),
                        and_(IngestionJob.status == "processing", IngestionJob.lease_expires_at <= now),
                    ),
                )
                .order_by(IngestionJob.available_at, IngestionJob.id)
                .limit(1)
                .with_for_update(skip_locked=True)
            )
            if job is None:
                return None
            job.status = "processing"
            job.attempts += 1
            job.lease_owner = worker_id
            job.lease_token = uuid4()
            job.lease_expires_at = now + timedelta(seconds=lease_seconds)
            job.error_code = None
            job.updated_at = now
            await session.flush()
            return job

    async def heartbeat_async(self, *, job_id: UUID, scope: str, lease_token: UUID, lease_seconds: int) -> bool:
        async with self._db.transaction_async() as session:
            now = await session.scalar(select(func.now()))
            result = await session.execute(
                update(IngestionJob)
                .where(
                    IngestionJob.id == job_id,
                    IngestionJob.deployment_scope == scope,
                    IngestionJob.status == "processing",
                    IngestionJob.lease_token == lease_token,
                    IngestionJob.lease_expires_at > now,
                )
                .values(lease_expires_at=now + timedelta(seconds=lease_seconds), updated_at=now)
            )
            return result.rowcount == 1

    async def complete_async(self, *, job_id: UUID, scope: str, lease_token: UUID) -> bool:
        async with self._db.transaction_async() as session:
            now = await session.scalar(select(func.now()))
            result = await session.execute(
                update(IngestionJob)
                .where(
                    IngestionJob.id == job_id,
                    IngestionJob.deployment_scope == scope,
                    IngestionJob.status == "processing",
                    IngestionJob.lease_token == lease_token,
                    IngestionJob.lease_expires_at > now,
                )
                .values(
                    status="completed",
                    lease_owner=None,
                    lease_token=None,
                    lease_expires_at=None,
                    error_code=None,
                    updated_at=now,
                )
            )
            return result.rowcount == 1

    async def fail_async(self, *, job_id: UUID, scope: str, lease_token: UUID, error_code: str) -> bool:
        async with self._db.transaction_async() as session:
            now = await session.scalar(select(func.now()))
            job = await session.scalar(
                select(IngestionJob)
                .where(
                    IngestionJob.id == job_id,
                    IngestionJob.deployment_scope == scope,
                    IngestionJob.status == "processing",
                    IngestionJob.lease_token == lease_token,
                    IngestionJob.lease_expires_at > now,
                )
                .with_for_update()
            )
            if job is None:
                return False
            exhausted = job.attempts >= job.max_attempts
            job.status = "dead_letter" if exhausted else "retry_wait"
            job.available_at = now if exhausted else now + timedelta(seconds=min(2**job.attempts, 300))
            job.lease_owner = None
            job.lease_token = None
            job.lease_expires_at = None
            job.error_code = error_code
            job.updated_at = now
            await session.flush()
            return True
