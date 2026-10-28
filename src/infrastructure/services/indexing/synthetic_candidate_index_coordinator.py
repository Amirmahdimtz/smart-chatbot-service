"""Phase07 experimental end-to-end *hidden* vector staging, never publication."""

from __future__ import annotations

from uuid import UUID

from src.core.services.indexing.index_manifest import (
    IndexContractError,
    IndexManifest,
    build_index_manifest,
    validate_embedding_vectors,
)
from src.infrastructure.providers.embedding.candidate_cpu_embedding_provider import CandidateCpuEmbeddingProvider
from src.infrastructure.providers.qdrant.index_staging_service import IndexStagingService
from src.infrastructure.repositories.indexing.postgres_index_source_repository import PostgresIndexSourceRepository
from src.infrastructure.utils.config_reader import ConfigReader


class SyntheticCandidateIndexCoordinator:
    """PG source → genuine pinned model vectors → Qdrant published=False.

    No approved-model claim, no visibility/alias transition, no durable queue.
    """

    def __init__(
        self,
        source_repository: PostgresIndexSourceRepository,
        embedding_provider: CandidateCpuEmbeddingProvider,
        staging_service: IndexStagingService,
        config_reader: ConfigReader,
    ):
        self._repository = source_repository
        self._embedding = embedding_provider
        self._stager = staging_service
        self._settings = config_reader.settings

    async def stage_version_async(
        self, *, version_id: UUID, principal_id: str, domain: str
    ) -> tuple[IndexManifest, list[str]]:
        if (
            self._settings.environment not in {"development", "integration"}
            or self._settings.deployment_zone != "internal"
            or not self._settings.ingestion.synthetic_only
        ):
            raise IndexContractError("experimental_indexing_not_authorized")
        snapshot = await self._repository.read_unpublished_async(
            version_id=version_id, principal_id=principal_id, domain=domain
        )
        manifest = build_index_manifest(
            document_id=snapshot.document_id,
            version_id=snapshot.version_id,
            scope=snapshot.scope,
            domain=snapshot.domain,
            classification=snapshot.classification,
            model_id=self._embedding.model_id,
            model_revision=self._embedding.revision,
            dimension=self._embedding.DIMENSION,
            distance="Cosine",
            schema_version=self._settings.qdrant.schema_version,
            chunks=snapshot.chunks,
        )
        vectors = await self._embedding.embed_async([item.canonical_text for item in snapshot.chunks], kind="passage")
        validated = validate_embedding_vectors(manifest, vectors)
        # Re-read after CPU inference: concurrent source changes/revocation must
        # fail closed before even unpublished vectors are written.
        before_stage = await self._repository.read_unpublished_async(
            version_id=version_id, principal_id=principal_id, domain=domain
        )
        if before_stage != snapshot:
            raise IndexContractError("source_changed_during_embedding")
        ids = await self._stager.stage_async(manifest, validated)
        # A concurrent revoke after writes cannot make vectors visible:
        # Qdrant published=False, and this recheck refuses success.
        after_stage = await self._repository.read_unpublished_async(
            version_id=version_id, principal_id=principal_id, domain=domain
        )
        if after_stage != snapshot:
            raise IndexContractError("source_changed_during_hidden_staging")
        return manifest, ids
