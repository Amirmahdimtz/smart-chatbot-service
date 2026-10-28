"""Durable, fenced Phase07 PostgreSQL indexing lifecycle. Synthetic only.

All publication decisions are authoritative PG transactions. The real Qdrant
side is intentionally non-transactional and must be reconciled after failures.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import and_, select

from src.core.services.indexing.index_manifest import IndexContractError, IndexManifest
from src.infrastructure.context.sql_db.psql_dbcontext import PsqlDbContext
from src.infrastructure.di.inject import inject
from src.infrastructure.models.entities import DocumentVersion, KnowledgeDocument, KnowledgeSource
from src.infrastructure.models.indexing import IndexJob, IndexManifestRecord, IndexPublication
from src.infrastructure.utils.config_reader import ConfigReader


def _manifest_json(manifest: IndexManifest) -> dict:
    data = asdict(manifest)
    data["id"] = str(manifest.id)
    data["document_id"] = str(manifest.document_id)
    data["version_id"] = str(manifest.version_id)
    data["chunk_ids"] = [str(chunk_id) for chunk_id in manifest.chunk_ids]
    return data


@inject
class IndexJobRepository:
    def __init__(self, db_context: PsqlDbContext, config_reader: ConfigReader):
        self._db = db_context
        self._config = config_reader.settings

    def _guard(self) -> None:
        s = self._config
        if (
            s.environment not in {"development", "integration"}
            or s.deployment_zone != "internal"
            or not s.database.enabled
            or not s.qdrant.enabled
            or not s.ingestion.synthetic_only
        ):
            raise IndexContractError("index_lifecycle_not_authorized")

    async def _authority(self, session, version_id: UUID, owner: str, domain: str, *, lock: bool):
        statement = (
            select(DocumentVersion, KnowledgeDocument, KnowledgeSource)
            .join(
                KnowledgeDocument,
                and_(
                    DocumentVersion.document_id == KnowledgeDocument.id,
                    DocumentVersion.deployment_scope == KnowledgeDocument.deployment_scope,
                ),
            )
            .join(
                KnowledgeSource,
                and_(
                    KnowledgeDocument.source_id == KnowledgeSource.id,
                    KnowledgeDocument.deployment_scope == KnowledgeSource.deployment_scope,
                ),
            )
            .where(
                DocumentVersion.id == version_id,
                DocumentVersion.deployment_scope == "internal",
                KnowledgeSource.owner_principal_id == owner,
                KnowledgeSource.domain == domain,
                KnowledgeSource.status == "active",
                KnowledgeSource.classification == "synthetic_unclassified",
                KnowledgeSource.policy_ref == "synthetic-only",
            )
        )
        if lock:
            statement = statement.with_for_update(of=DocumentVersion)
        return (await session.execute(statement)).one_or_none()

    async def enqueue_async(self, manifest: IndexManifest, *, principal_id: str) -> UUID:
        self._guard()
        if (
            not isinstance(manifest, IndexManifest)
            or not isinstance(principal_id, str)
            or not principal_id.strip()
            or len(principal_id) > 255
            or manifest.scope != "internal"
            or manifest.classification != "synthetic_unclassified"
            or not manifest.model_revision
            or manifest.embedding_dimension != self._config.qdrant.dimension
            or manifest.distance != self._config.qdrant.distance
            or manifest.schema_version != self._config.qdrant.schema_version
        ):
            raise IndexContractError("invalid_index_job_request")
        async with self._db.transaction_async() as session:
            authority = await self._authority(
                session, manifest.version_id, principal_id, manifest.domain, lock=True
            )
            if authority is None or authority[0].state != "awaiting_approval" or authority[1].id != manifest.document_id:
                raise IndexContractError("index_source_not_eligible")
            existing = await session.scalar(
                select(IndexJob).where(IndexJob.version_id == manifest.version_id).with_for_update()
            )
            if existing:
                if (
                    existing.manifest_id != manifest.id
                    or existing.manifest_sha256 != manifest.canonical_checksum_sha256
                    or existing.owner_principal_id != principal_id
                    or existing.domain != manifest.domain
                    or existing.status in {"dead", "revoked"}
                ):
                    raise IndexContractError("index_job_manifest_conflict")
                return existing.id
            job = IndexJob(
                id=uuid4(),
                document_id=manifest.document_id,
                version_id=manifest.version_id,
                deployment_scope="internal",
                owner_principal_id=principal_id,
                domain=manifest.domain,
                manifest_id=manifest.id,
                manifest_sha256=manifest.canonical_checksum_sha256,
                model_id=manifest.model_id,
                model_revision=manifest.model_revision,
                embedding_dimension=manifest.embedding_dimension,
                chunk_count=manifest.chunk_count,
                status="queued",
                attempts=0,
                max_attempts=3,
            )
            session.add(job)
            await session.flush()
            session.add(
                IndexManifestRecord(
                    id=uuid4(),
                    job_id=job.id,
                    manifest_sha256=manifest.canonical_checksum_sha256,
                    manifest_json=_manifest_json(manifest),
                    point_ids=[],
                )
            )
            return job.id

    async def claim_async(self, job_id: UUID, *, principal_id: str, lease_seconds: int = 90) -> UUID | None:
        self._guard()
        if not isinstance(job_id, UUID) or not 15 <= lease_seconds <= 600:
            raise IndexContractError("invalid_index_claim")
        async with self._db.transaction_async() as session:
            job = await session.scalar(select(IndexJob).where(IndexJob.id == job_id).with_for_update())
            if job is None or job.owner_principal_id != principal_id or job.deployment_scope != "internal":
                return None
            now = datetime.now(UTC)
            retryable = job.status == "queued" or (
                job.status == "leased" and job.lease_expires_at is not None and job.lease_expires_at <= now
            )
            if not retryable or job.attempts >= job.max_attempts:
                return None
            authority = await self._authority(session, job.version_id, principal_id, job.domain, lock=False)
            if authority is None or authority[0].state != "awaiting_approval":
                return None
            token = uuid4()
            job.status = "leased"
            job.attempts += 1
            job.lease_token = token
            job.lease_expires_at = now + timedelta(seconds=lease_seconds)
            job.error_code = None
            return token

    async def finish_async(
        self, job_id: UUID, *, lease_token: UUID, manifest: IndexManifest, point_ids: list[str]
    ) -> bool:
        self._guard()
        if (
            not isinstance(lease_token, UUID)
            or not isinstance(manifest, IndexManifest)
            or len(point_ids) != manifest.chunk_count
            or len(set(point_ids)) != len(point_ids)
            or any(not isinstance(pid, str) or len(pid) > 80 for pid in point_ids)
        ):
            raise IndexContractError("invalid_staged_manifest")
        async with self._db.transaction_async() as session:
            job = await session.scalar(select(IndexJob).where(IndexJob.id == job_id).with_for_update())
            now = datetime.now(UTC)
            if (
                job is None
                or job.status != "leased"
                or job.lease_token != lease_token
                or job.lease_expires_at is None
                or job.lease_expires_at <= now
                or job.manifest_id != manifest.id
                or job.manifest_sha256 != manifest.canonical_checksum_sha256
                or job.chunk_count != manifest.chunk_count
                or job.model_id != manifest.model_id
                or job.model_revision != manifest.model_revision
            ):
                return False
            authority = await self._authority(session, job.version_id, job.owner_principal_id, job.domain, lock=False)
            if authority is None or authority[0].state != "awaiting_approval":
                return False
            record = await session.scalar(select(IndexManifestRecord).where(IndexManifestRecord.job_id == job.id))
            if record is None or record.manifest_json != _manifest_json(manifest):
                return False
            record.point_ids = point_ids
            job.status = "staged"
            job.lease_token = None
            job.lease_expires_at = None
            return True

    async def fail_async(self, job_id: UUID, *, lease_token: UUID, error_code: str, retriable: bool) -> bool:
        self._guard()
        if not isinstance(error_code, str) or not error_code or len(error_code) > 48:
            raise IndexContractError("invalid_index_error")
        async with self._db.transaction_async() as session:
            job = await session.scalar(select(IndexJob).where(IndexJob.id == job_id).with_for_update())
            if job is None or job.status != "leased" or job.lease_token != lease_token:
                return False
            if job.lease_expires_at is None or job.lease_expires_at <= datetime.now(UTC):
                return False
            job.status = "queued" if retriable and job.attempts < job.max_attempts else "dead"
            job.lease_token = None
            job.lease_expires_at = None
            job.error_code = error_code
            return True

    async def approve_synthetic_async(
        self, job_id: UUID, *, approver_id: str, approval_ref: str, expected_digest: str
    ) -> bool:
        """Distinct synthetic reviewer only; NOT an organizational IdP approval."""
        self._guard()
        if (
            not approver_id
            or len(approver_id) > 255
            or not approval_ref
            or len(approval_ref) > 128
            or not isinstance(expected_digest, str)
            or len(expected_digest) != 64
        ):
            raise IndexContractError("invalid_synthetic_approval")
        async with self._db.transaction_async() as session:
            job = await session.scalar(select(IndexJob).where(IndexJob.id == job_id).with_for_update())
            if (
                job is None
                or job.status != "staged"
                or job.owner_principal_id == approver_id
                or job.manifest_sha256 != expected_digest
            ):
                return False
            auth = await self._authority(session, job.version_id, job.owner_principal_id, job.domain, lock=True)
            if auth is None or auth[0].state != "awaiting_approval":
                return False
            record = await session.scalar(select(IndexManifestRecord).where(IndexManifestRecord.job_id == job.id))
            if record is None or len(record.point_ids) != job.chunk_count:
                return False
            job.status = "approved"
            job.approved_by = approver_id
            job.approval_ref = approval_ref
            return True

    async def get_approved_async(self, job_id: UUID) -> tuple[IndexJob, IndexManifestRecord] | None:
        self._guard()
        async with self._db.transaction_async() as session:
            row = (
                await session.execute(
                    select(IndexJob, IndexManifestRecord)
                    .join(IndexManifestRecord, IndexManifestRecord.job_id == IndexJob.id)
                    .where(IndexJob.id == job_id, IndexJob.status == "approved")
                )
            ).one_or_none()
            return row

    async def publish_authoritative_async(self, job_id: UUID) -> tuple[bool, UUID | None]:
        """PG-visible version cutover is atomic; Qdrant alone NEVER authorizes."""
        self._guard()
        async with self._db.transaction_async() as session:
            initial = await session.get(IndexJob, job_id)
            if initial is None:
                return False, None
            # Document is the serialization mutex for publish/revoke/reindex.
            document = await session.scalar(
                select(KnowledgeDocument).where(KnowledgeDocument.id == initial.document_id).with_for_update()
            )
            if document is None:
                return False, None
            job = await session.scalar(select(IndexJob).where(IndexJob.id == job_id).with_for_update())
            if job is None or job.status != "approved" or not job.approved_by or not job.approval_ref:
                return False, None
            authority = await self._authority(
                session, job.version_id, job.owner_principal_id, job.domain, lock=True
            )
            if authority is None or authority[0].state != "awaiting_approval":
                return False, None
            receipt = await session.scalar(
                select(IndexManifestRecord).where(IndexManifestRecord.job_id == job.id)
            )
            if receipt is None or receipt.manifest_sha256 != job.manifest_sha256 or len(receipt.point_ids) != job.chunk_count:
                return False, None
            pointer = await session.get(IndexPublication, document.id)
            previous = pointer.active_version_id if pointer else None
            if previous is not None and previous != job.version_id:
                prior = await session.get(DocumentVersion, previous)
                if prior and prior.state == "published":
                    prior.state = "superseded"
                previous_job = await session.scalar(
                    select(IndexJob).where(IndexJob.version_id == previous).with_for_update()
                )
                if previous_job is not None and previous_job.status == "published":
                    previous_job.status = "revoked"
                    previous_job.cleanup_pending = True
            if pointer is None:
                session.add(
                    IndexPublication(
                        document_id=job.document_id,
                        deployment_scope="internal",
                        active_version_id=job.version_id,
                        generation=1,
                    )
                )
            else:
                pointer.active_version_id = job.version_id
                pointer.generation += 1
            authority[0].state = "published"
            job.status = "published"
            return True, previous

    async def revoke_authoritative_async(self, version_id: UUID, *, owner_id: str, domain: str) -> bool:
        """PG-first revoke is authoritative even when Qdrant cleanup is offline."""
        self._guard()
        async with self._db.transaction_async() as session:
            prelim = await session.get(DocumentVersion, version_id)
            if prelim is None:
                return False
            doc = await session.scalar(
                select(KnowledgeDocument).where(KnowledgeDocument.id == prelim.document_id).with_for_update()
            )
            if doc is None:
                return False
            authority = await self._authority(session, version_id, owner_id, domain, lock=True)
            if authority is None or authority[0].state not in {"published", "awaiting_approval"}:
                return False
            pointer = await session.get(IndexPublication, doc.id)
            if pointer is not None and pointer.active_version_id == version_id:
                pointer.active_version_id = None
                pointer.generation += 1
            authority[0].state = "revoked"
            job = await session.scalar(
                select(IndexJob).where(IndexJob.version_id == version_id).with_for_update()
            )
            if job is not None:
                job.status = "revoked"
                job.lease_token = None
                job.lease_expires_at = None
                job.cleanup_pending = True
            return True

    async def cleanup_receipt_async(self, version_id: UUID) -> tuple[IndexJob, IndexManifestRecord] | None:
        """Durable Qdrant cleanup outbox; can be retried after a service outage."""
        self._guard()
        async with self._db.transaction_async() as session:
            return (
                await session.execute(
                    select(IndexJob, IndexManifestRecord)
                    .join(IndexManifestRecord, IndexManifestRecord.job_id == IndexJob.id)
                    .where(IndexJob.version_id == version_id, IndexJob.cleanup_pending.is_(True))
                )
            ).one_or_none()

    async def finish_cleanup_async(self, job_id: UUID) -> bool:
        self._guard()
        async with self._db.transaction_async() as session:
            job = await session.scalar(select(IndexJob).where(IndexJob.id == job_id).with_for_update())
            if job is None or not job.cleanup_pending or job.status != "revoked":
                return False
            job.cleanup_pending = False
            return True

    async def current_version_async(self, document_id: UUID) -> UUID | None:
        """Authoritative public-facing gates must check source and version too."""
        self._guard()
        async with self._db.transaction_async() as session:
            pointer = await session.get(IndexPublication, document_id)
            return pointer.active_version_id if pointer is not None else None
