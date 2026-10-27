"""Scoped durable ingestion transactions. PostgreSQL is the job source of truth."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import and_, delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.context.sql_db.psql_dbcontext import PsqlDbContext
from src.infrastructure.di.inject import inject
from src.infrastructure.models.entities import DocumentVersion, KnowledgeChunk, KnowledgeDocument, KnowledgeSource
from src.infrastructure.models.ingestion import IngestionAuditEvent, IngestionJob
from src.infrastructure.repositories.base.base_repository import BaseRepository


@inject
class IngestionRepository(BaseRepository[IngestionJob]):
    def __init__(self, db_context: PsqlDbContext):
        super().__init__(db_context=db_context, model=IngestionJob)

    async def insert_async(self, entity, *, session: AsyncSession | None = None):
        raise PermissionError("Use scoped ingestion operations")

    async def get_by_id_async(self, entity_id, *, session: AsyncSession | None = None):
        raise PermissionError("Use scoped ingestion operations")

    async def get_all_async(self, *, session: AsyncSession | None = None):
        raise PermissionError("Use scoped ingestion operations")

    async def update_async(self, entity, *, session: AsyncSession | None = None):
        raise PermissionError("Use scoped ingestion operations")

    async def delete_async(self, entity_id, *, session: AsyncSession | None = None):
        raise PermissionError("Use scoped ingestion operations")

    def _audit(self, session, job: IngestionJob | None, source_id: UUID, scope: str, actor: str, event: str, code=None):
        session.add(
            IngestionAuditEvent(
                job_id=job.id if job else None,
                source_id=source_id,
                deployment_scope=scope,
                actor_ref=actor,
                event=event,
                code=code,
            )
        )

    async def create_source_async(
        self, actor: str, scope: str, domain: str, max_file_bytes: int | None = None
    ) -> KnowledgeSource:
        async with self._db.transaction_async() as session:
            source = KnowledgeSource(
                owner_principal_id=actor,
                deployment_scope=scope,
                domain=domain,
                classification="synthetic_unclassified",
                policy_ref="synthetic-only",
                max_file_bytes=max_file_bytes,
            )
            session.add(source)
            await session.flush()
            self._audit(session, None, source.id, scope, actor, "source_created")
            return source

    async def get_source_owned_async(self, source_id: UUID, actor: str, scope: str) -> KnowledgeSource | None:
        async with self._db.transaction_async() as session:
            return await session.scalar(
                select(KnowledgeSource).where(
                    KnowledgeSource.id == source_id,
                    KnowledgeSource.owner_principal_id == actor,
                    KnowledgeSource.deployment_scope == scope,
                )
            )

    async def disable_source_owned_async(self, source_id: UUID, actor: str, scope: str) -> KnowledgeSource | None:
        """Owner-only, audited, idempotent disable; no implicit deletion or publication."""
        async with self._db.transaction_async() as session:
            source = await session.scalar(
                select(KnowledgeSource)
                .where(
                    KnowledgeSource.id == source_id,
                    KnowledgeSource.owner_principal_id == actor,
                    KnowledgeSource.deployment_scope == scope,
                )
                .with_for_update()
            )
            if source is not None and source.status != "disabled":
                source.status = "disabled"
                self._audit(session, None, source.id, scope, actor, "source_disabled")
            return source

    async def stage_async(
        self,
        source_id: UUID,
        actor: str,
        scope: str,
        filename: str,
        content_type: str,
        size: int,
        checksum: str,
        idempotency_key: str,
        max_attempts: int,
    ) -> tuple[IngestionJob, DocumentVersion, bool]:
        async with self._db.transaction_async() as session:
            source = await session.scalar(
                select(KnowledgeSource)
                .where(
                    KnowledgeSource.id == source_id,
                    KnowledgeSource.owner_principal_id == actor,
                    KnowledgeSource.deployment_scope == scope,
                    KnowledgeSource.status == "active",
                )
                .with_for_update()
            )
            if source is None:
                raise PermissionError("Source unavailable")
            prior = await session.scalar(
                select(IngestionJob).where(
                    IngestionJob.source_id == source.id,
                    IngestionJob.deployment_scope == scope,
                    IngestionJob.owner_principal_id == actor,
                    IngestionJob.idempotency_key == idempotency_key,
                )
            )
            if prior:
                if prior.checksum_sha256 != checksum:
                    raise ValueError("Idempotency key conflict")
                version = await session.get(DocumentVersion, prior.version_id)
                if (
                    prior.status == "dead"
                    and prior.attempts == 0
                    and prior.error_code in {"storage_unavailable", "staging_abandoned"}
                ):
                    prior.status, prior.error_code, version.state = "staging", None, "draft"
                    self._audit(session, prior, source.id, scope, actor, "staging_retried")
                    return prior, version, True
                return prior, version, False
            repeated = await session.scalar(
                select(IngestionJob).where(
                    IngestionJob.source_id == source.id,
                    IngestionJob.deployment_scope == scope,
                    IngestionJob.checksum_sha256 == checksum,
                )
            )
            if repeated:
                # Dedup must not silently alias a new key to another request.
                # Otherwise replaying that key with different bytes would create
                # a new document instead of detecting idempotency-key misuse.
                raise ValueError("Duplicate content requires the original idempotency key")
            document = KnowledgeDocument(
                source_id=source.id, deployment_scope=scope, title=filename, classification=None
            )
            session.add(document)
            await session.flush()
            key = f"quarantine/{scope}/{uuid4()}"
            version = DocumentVersion(
                document_id=document.id,
                deployment_scope=scope,
                version_number=1,
                checksum_sha256=checksum,
                state="draft",
                safe_filename=filename,
                content_type=content_type,
                byte_size=size,
                object_key=key,
            )
            session.add(version)
            await session.flush()
            job = IngestionJob(
                source_id=source.id,
                version_id=version.id,
                deployment_scope=scope,
                owner_principal_id=actor,
                idempotency_key=idempotency_key,
                checksum_sha256=checksum,
                status="staging",
                max_attempts=max_attempts,
            )
            session.add(job)
            await session.flush()
            self._audit(session, job, source.id, scope, actor, "upload_staged")
            return job, version, True

    async def mark_queued_async(self, job_id: UUID, actor: str, scope: str) -> bool:
        async with self._db.transaction_async() as session:
            job = await session.scalar(
                select(IngestionJob)
                .where(
                    IngestionJob.id == job_id,
                    IngestionJob.owner_principal_id == actor,
                    IngestionJob.deployment_scope == scope,
                )
                .with_for_update()
            )
            if job is None or job.status != "staging":
                return False
            job.status = "queued"
            self._audit(session, job, job.source_id, scope, actor, "queued")
            return True

    async def fail_staging_async(self, job_id: UUID, actor: str, scope: str, code: str) -> None:
        async with self._db.transaction_async() as session:
            job = await session.scalar(
                select(IngestionJob)
                .where(
                    IngestionJob.id == job_id,
                    IngestionJob.owner_principal_id == actor,
                    IngestionJob.deployment_scope == scope,
                )
                .with_for_update()
            )
            if job and job.status == "staging":
                job.status, job.error_code = "dead", code
                version = await session.get(DocumentVersion, job.version_id)
                version.state = "failed"
                self._audit(session, job, job.source_id, scope, actor, "upload_failed", code)

    async def get_job_owned_async(self, job_id: UUID, actor: str, scope: str):
        async with self._db.transaction_async() as session:
            job = await session.scalar(
                select(IngestionJob).where(
                    IngestionJob.id == job_id,
                    IngestionJob.owner_principal_id == actor,
                    IngestionJob.deployment_scope == scope,
                )
            )
            if job is None:
                return None
            return job, await session.get(DocumentVersion, job.version_id)

    async def get_version_owned_async(self, version_id: UUID, actor: str, scope: str):
        async with self._db.transaction_async() as session:
            return await session.scalar(
                select(DocumentVersion)
                .join(KnowledgeDocument, DocumentVersion.document_id == KnowledgeDocument.id)
                .join(KnowledgeSource, KnowledgeDocument.source_id == KnowledgeSource.id)
                .where(
                    DocumentVersion.id == version_id,
                    DocumentVersion.deployment_scope == scope,
                    KnowledgeSource.owner_principal_id == actor,
                    KnowledgeSource.deployment_scope == scope,
                )
            )

    async def cancel_async(self, job_id: UUID, actor: str, scope: str) -> bool:
        async with self._db.transaction_async() as session:
            job = await session.scalar(
                select(IngestionJob)
                .where(
                    IngestionJob.id == job_id,
                    IngestionJob.owner_principal_id == actor,
                    IngestionJob.deployment_scope == scope,
                )
                .with_for_update()
            )
            if job is None or job.status in {"completed", "dead", "cancelled"}:
                return False
            job.status = "cancelled"
            job.lease_owner = None
            job.lease_expires_at = None
            version = await session.get(DocumentVersion, job.version_id)
            version.state = "failed"
            self._audit(session, job, job.source_id, scope, actor, "cancelled")
            return True

    async def claim_async(self, worker_id: str, scope: str, lease_seconds: int):
        async with self._db.transaction_async() as session:
            job = await session.scalar(
                select(IngestionJob)
                .where(
                    IngestionJob.deployment_scope == scope,
                    IngestionJob.attempts < IngestionJob.max_attempts,
                    or_(
                        IngestionJob.status == "queued",
                        and_(IngestionJob.status == "retry_wait", IngestionJob.next_retry_at <= func.now()),
                        and_(IngestionJob.status == "leased", IngestionJob.lease_expires_at <= func.now()),
                    ),
                )
                .order_by(IngestionJob.created_at, IngestionJob.id)
                .limit(1)
                .with_for_update(skip_locked=True)
            )
            if job is None:
                return None
            token = f"{worker_id}:{uuid4()}"
            job.status, job.lease_owner = "leased", token
            job.attempts += 1
            job.heartbeat_at = func.now()
            job.lease_expires_at = func.now() + lease_seconds * timedelta(seconds=1)
            job.next_retry_at = None
            version = await session.get(DocumentVersion, job.version_id)
            version.state = "processing"
            self._audit(session, job, job.source_id, scope, worker_id, "claimed")
            await session.flush()
            return job.id, token, version.object_key, job.checksum_sha256, version.byte_size, version.id, version.content_type

    async def heartbeat_async(self, job_id: UUID, token: str, lease_seconds: int) -> bool:
        async with self._db.transaction_async() as session:
            statement = (
                update(IngestionJob)
                .where(
                    IngestionJob.id == job_id,
                    IngestionJob.status == "leased",
                    IngestionJob.lease_owner == token,
                    IngestionJob.lease_expires_at > func.now(),
                )
                .values(
                    heartbeat_at=func.now(),
                    lease_expires_at=func.now() + lease_seconds * timedelta(seconds=1),
                )
            )
            result = await session.execute(statement)
            return result.rowcount == 1

    async def finish_async(
        self, job_id: UUID, token: str, success: bool, error_code: str | None = None, retriable: bool = False,
        chunks: list | None = None,
    ) -> bool:
        async with self._db.transaction_async() as session:
            job = await session.scalar(select(IngestionJob).where(IngestionJob.id == job_id).with_for_update())
            db_now = await session.scalar(select(func.now()))
            if (
                job is None
                or job.status != "leased"
                or job.lease_owner != token
                or job.lease_expires_at is None
                or job.lease_expires_at <= db_now
            ):
                return False
            version = await session.get(DocumentVersion, job.version_id)
            if success:
                # All source-mapped chunks and the final job/version states commit
                # under the same valid lease token and PostgreSQL transaction.
                if not chunks or len(chunks) > 4096:
                    return False
                await session.execute(
                    delete(KnowledgeChunk).where(
                        KnowledgeChunk.version_id == version.id,
                        KnowledgeChunk.deployment_scope == job.deployment_scope,
                    )
                )
                session.add_all(
                    [
                        KnowledgeChunk(
                            id=item.id,
                            version_id=version.id,
                            deployment_scope=job.deployment_scope,
                            ordinal=item.ordinal,
                            checksum_sha256=item.checksum,
                            original_text=item.original,
                            canonical_text=item.canonical,
                            page_number=item.page,
                            source_start=item.start,
                            source_end=item.end,
                            section_title=item.section,
                            extractor_method=item.method,
                            processor_version=item.processor_version,
                        )
                        for item in chunks
                    ]
                )
                job.status, job.error_code, version.state = "completed", None, "awaiting_approval"
            elif retriable and job.attempts < job.max_attempts:
                job.status, job.error_code = "retry_wait", error_code
                job.next_retry_at = datetime.now(UTC) + timedelta(seconds=min(60, 2**job.attempts))
            else:
                job.status, job.error_code, version.state = "dead", error_code, "failed"
            job.lease_owner = None
            job.lease_expires_at = None
            self._audit(session, job, job.source_id, job.deployment_scope, "worker", job.status, error_code)
            return True

    async def list_stale_staging_async(self, scope: str, age_seconds: int = 30):
        """Only read committed stale intents. Never hold a transaction across object network I/O."""
        async with self._db.transaction_async() as session:
            rows = await session.execute(
                select(
                    IngestionJob.id,
                    IngestionJob.owner_principal_id,
                    IngestionJob.checksum_sha256,
                    IngestionJob.created_at,
                    DocumentVersion.object_key,
                    DocumentVersion.byte_size,
                )
                .join(DocumentVersion, IngestionJob.version_id == DocumentVersion.id)
                .where(
                    IngestionJob.deployment_scope == scope,
                    IngestionJob.status == "staging",
                    IngestionJob.created_at < func.now() - timedelta(seconds=age_seconds),
                )
                .order_by(IngestionJob.created_at)
                .limit(20)
            )
            return [tuple(x) for x in rows.all()]

    async def exhaust_expired_async(self, scope: str) -> int:
        """Terminally fence leases after their final attempted execution."""
        async with self._db.transaction_async() as session:
            jobs = await session.scalars(
                select(IngestionJob)
                .where(
                    IngestionJob.deployment_scope == scope,
                    IngestionJob.status == "leased",
                    IngestionJob.lease_expires_at <= func.now(),
                    IngestionJob.attempts >= IngestionJob.max_attempts,
                )
                .limit(20)
                .with_for_update(skip_locked=True)
            )
            count = 0
            for job in jobs:
                job.status, job.error_code = "dead", "lease_expired"
                job.lease_owner = None
                job.lease_expires_at = None
                version = await session.get(DocumentVersion, job.version_id)
                version.state = "failed"
                self._audit(session, job, job.source_id, scope, "worker", "dead", job.error_code)
                count += 1
            return count
