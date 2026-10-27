"""Phase07 safe synthetic staging of validated embeddings in a hidden Qdrant index.

No publication API exists here. A real approved model and PostgreSQL approval
state are prerequisites for the eventual publication coordinator.
"""

from __future__ import annotations

from collections.abc import Sequence

from src.core.services.indexing.index_manifest import (
    IndexContractError,
    IndexManifest,
    ValidatedVector,
)
from src.infrastructure.di.inject import inject
from src.infrastructure.providers.qdrant.qdrant_provider import (
    QdrantProvider,
    VectorRecord,
)
from src.infrastructure.utils.config_reader import ConfigReader


@inject
class IndexStagingService:
    def __init__(self, qdrant_provider: QdrantProvider, config_reader: ConfigReader):
        self._qdrant = qdrant_provider
        self._config = config_reader.settings

    async def stage_async(
        self, manifest: IndexManifest, vectors: Sequence[ValidatedVector]
    ) -> list[str]:
        """Idempotent wait=True upsert, always unpublished, bounded by provider batch size.

        This method never switches aliases, marks a version published, or
        bypasses the unavailable D-03 model-selection and approval gates.
        """
        settings = self._config
        if (
            not isinstance(manifest, IndexManifest)
            or not settings.qdrant.enabled
            or not settings.ingestion.synthetic_only
            or settings.environment not in {"development", "integration"}
            or manifest.scope != settings.deployment_zone
            or manifest.classification != "synthetic_unclassified"
            or manifest.schema_version != settings.qdrant.schema_version
            or manifest.embedding_dimension != settings.qdrant.dimension
            or manifest.distance != settings.qdrant.distance
            or len(vectors) != manifest.chunk_count
            or tuple(v.chunk_id for v in vectors) != manifest.chunk_ids
        ):
            raise IndexContractError("index_staging_not_authorized")
        await self._qdrant.ensure_collection_async()
        result: list[str] = []
        batch_size = settings.qdrant.batch_size
        for start in range(0, len(vectors), batch_size):
            chunk = vectors[start : start + batch_size]
            records = [
                VectorRecord(
                    chunk_id=item.chunk_id,
                    document_id=manifest.document_id,
                    document_version_id=manifest.version_id,
                    domain=manifest.domain,
                    classification=manifest.classification,
                    vector=item.values,
                    published=False,
                )
                for item in chunk
            ]
            result.extend(await self._qdrant.upsert_async(records))
        if len(result) != manifest.chunk_count:
            raise IndexContractError("index_staging_incomplete")
        return result
