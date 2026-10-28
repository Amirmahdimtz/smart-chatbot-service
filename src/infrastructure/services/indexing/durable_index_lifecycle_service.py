"""Phase07 fail-closed synthetic job worker and PG-authoritative publication.

The approval path here is restricted to Development synthetic CI, not to an
organizational IdP or production. Cross-system commit cannot be truly atomic:
PG is the only visibility authority; Qdrant is indexed candidate storage.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from src.core.services.indexing.index_manifest import (
    IndexContractError,
    IndexManifest,
    build_index_manifest,
    validate_embedding_vectors,
)
from src.infrastructure.providers.embedding.candidate_cpu_embedding_provider import CandidateCpuEmbeddingProvider
from src.infrastructure.providers.qdrant.index_staging_service import IndexStagingService
from src.infrastructure.providers.qdrant.qdrant_provider import QdrantProvider, QdrantUnavailable
from src.infrastructure.repositories.indexing.index_job_repository import IndexJobRepository
from src.infrastructure.repositories.indexing.postgres_index_source_repository import PostgresIndexSourceRepository


@dataclass(frozen=True)
class RevocationResult:
    pg_revoked: bool
    qdrant_cleanup_pending: bool


class DurableIndexLifecycleService:
    def __init__(
        self,
        sources: PostgresIndexSourceRepository,
        jobs: IndexJobRepository,
        embedding: CandidateCpuEmbeddingProvider,
        staging: IndexStagingService,
        qdrant: QdrantProvider,
    ):
        self._sources = sources
        self._jobs = jobs
        self._embedding = embedding
        self._staging = staging
        self._qdrant = qdrant

    async def enqueue_async(self, *, version_id: UUID, principal_id: str, domain: str) -> tuple[UUID, IndexManifest]:
        snapshot = await self._sources.read_unpublished_async(
            version_id=version_id, principal_id=principal_id, domain=domain
        )
        manifest = build_index_manifest(
            document_id=snapshot.document_id,
            version_id=version_id,
            scope=snapshot.scope,
            domain=snapshot.domain,
            classification=snapshot.classification,
            model_id=self._embedding.model_id,
            model_revision=self._embedding.revision,
            dimension=self._embedding.DIMENSION,
            distance="Cosine",
            schema_version=self._staging._config.qdrant.schema_version,
            chunks=snapshot.chunks,
        )
        job_id = await self._jobs.enqueue_async(manifest, principal_id=principal_id)
        return job_id, manifest

    async def stage_claimed_async(self, *, job_id: UUID, manifest: IndexManifest, principal_id: str) -> tuple[str, ...]:
        token = await self._jobs.claim_async(job_id, principal_id=principal_id)
        if token is None:
            raise IndexContractError("index_job_not_claimable")
        try:
            before = await self._sources.read_unpublished_async(
                version_id=manifest.version_id, principal_id=principal_id, domain=manifest.domain
            )
            regenerated = build_index_manifest(
                document_id=before.document_id,
                version_id=before.version_id,
                scope=before.scope,
                domain=before.domain,
                classification=before.classification,
                model_id=self._embedding.model_id,
                model_revision=self._embedding.revision,
                dimension=self._embedding.DIMENSION,
                distance="Cosine",
                schema_version=self._staging._config.qdrant.schema_version,
                chunks=before.chunks,
            )
            if regenerated != manifest:
                raise IndexContractError("index_manifest_drift")
            vectors = await self._embedding.embed_async(
                [chunk.canonical_text for chunk in before.chunks], kind="passage"
            )
            checked = validate_embedding_vectors(manifest, vectors)
            if (
                await self._sources.read_unpublished_async(
                    version_id=manifest.version_id, principal_id=principal_id, domain=manifest.domain
                )
                != before
            ):
                raise IndexContractError("source_changed_before_upsert")
            ids = await self._staging.stage_async(manifest, checked)
            if not await self._qdrant.verify_manifest_points_async(
                point_ids=ids,
                document_id=manifest.document_id,
                version_id=manifest.version_id,
                domain=manifest.domain,
                published=False,
            ):
                raise IndexContractError("qdrant_partial_or_drifted")
            if (
                await self._sources.read_unpublished_async(
                    version_id=manifest.version_id, principal_id=principal_id, domain=manifest.domain
                )
                != before
            ):
                raise IndexContractError("source_changed_after_upsert")
            if not await self._jobs.finish_async(job_id, lease_token=token, manifest=manifest, point_ids=ids):
                raise IndexContractError("stale_index_lease_or_source")
            return tuple(ids)
        except Exception:
            # A failed/partial Qdrant write is always untrusted and unpublished.
            await self._jobs.fail_async(job_id, lease_token=token, error_code="index_stage_failed", retriable=True)
            raise

    async def approve_synthetic_async(self, *, job_id: UUID, approver_id: str, approval_ref: str, digest: str) -> bool:
        return await self._jobs.approve_synthetic_async(
            job_id, approver_id=approver_id, approval_ref=approval_ref, expected_digest=digest
        )

    async def publish_synthetic_async(self, *, job_id: UUID) -> bool:
        row = await self._jobs.get_approved_async(job_id)
        if row is None:
            return False
        job, receipt = row
        if not await self._qdrant.verify_manifest_points_async(
            point_ids=receipt.point_ids,
            document_id=job.document_id,
            version_id=job.version_id,
            domain=job.domain,
            published=False,
        ):
            raise IndexContractError("publish_manifest_not_consistent")
        # Before PG publication the Qdrant points are still *unauthorized*.
        await self._qdrant.activate_collection_async()
        await self._qdrant.mark_manifest_visible_async(
            point_ids=receipt.point_ids,
            document_id=job.document_id,
            version_id=job.version_id,
            domain=job.domain,
            visible=True,
        )
        try:
            successful, previous = await self._jobs.publish_authoritative_async(job_id)
            if not successful:
                raise IndexContractError("publication_race_or_revoked")
        except Exception:
            # Best-effort compensation, PG still refuses authorization if it fails.
            try:
                await self._qdrant.mark_manifest_visible_async(
                    point_ids=receipt.point_ids,
                    document_id=job.document_id,
                    version_id=job.version_id,
                    domain=job.domain,
                    visible=False,
                )
            except Exception:
                pass
            raise
        # Old version is already superseded in PG and no longer authorized,
        # even if the old Qdrant cleanup outbox has not yet run.
        return True

    async def revoke_first_async(self, *, version_id: UUID, owner_id: str, domain: str) -> RevocationResult:
        revoked = await self._jobs.revoke_authoritative_async(version_id, owner_id=owner_id, domain=domain)
        if not revoked:
            return RevocationResult(False, False)
        try:
            done = await self.cleanup_revoked_async(version_id=version_id)
        except (QdrantUnavailable, IndexContractError):
            done = False
        return RevocationResult(True, not done)

    async def cleanup_revoked_async(self, *, version_id: UUID) -> bool:
        receipt = await self._jobs.cleanup_receipt_async(version_id)
        if receipt is None:
            return True
        job, manifest = receipt
        if await self._qdrant.verify_manifest_points_async(
            point_ids=manifest.point_ids,
            document_id=job.document_id,
            version_id=job.version_id,
            domain=job.domain,
            published=True,
        ):
            await self._qdrant.mark_manifest_visible_async(
                point_ids=manifest.point_ids,
                document_id=job.document_id,
                version_id=job.version_id,
                domain=job.domain,
                visible=False,
            )
        elif not await self._qdrant.verify_manifest_points_async(
            point_ids=manifest.point_ids,
            document_id=job.document_id,
            version_id=job.version_id,
            domain=job.domain,
            published=False,
        ):
            raise IndexContractError("qdrant_cleanup_inconsistent")
        return await self._jobs.finish_cleanup_async(job.id)
