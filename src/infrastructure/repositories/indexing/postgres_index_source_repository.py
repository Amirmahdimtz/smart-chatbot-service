"""Authoritative PostgreSQL snapshot for synthetic, NOT-YET-published index staging.

Read-side only. No approval, visibility transition, or new durable index job
is implied; all such changes require the Phase07 publication coordinator.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import and_, select

from src.core.services.indexing.index_manifest import IndexContractError, IndexSourceChunk
from src.infrastructure.context.sql_db.psql_dbcontext import PsqlDbContext
from src.infrastructure.di.inject import inject
from src.infrastructure.models.entities import DocumentVersion, KnowledgeChunk, KnowledgeDocument, KnowledgeSource
from src.infrastructure.utils.config_reader import ConfigReader


@dataclass(frozen=True)
class IndexSourceSnapshot:
    version_id: UUID
    document_id: UUID
    scope: str
    domain: str
    classification: str
    chunks: tuple[IndexSourceChunk, ...]


@inject
class PostgresIndexSourceRepository:
    def __init__(self, db_context: PsqlDbContext, config_reader: ConfigReader):
        self._db = db_context
        self._settings = config_reader.settings

    async def read_unpublished_async(self, *, version_id: UUID, principal_id: str, domain: str) -> IndexSourceSnapshot:
        s = self._settings
        if (
            not isinstance(version_id, UUID)
            or not isinstance(principal_id, str)
            or not principal_id.strip()
            or len(principal_id) > 255
            or not isinstance(domain, str)
            or not 1 <= len(domain) <= 64
            or not all(c.isascii() and (c.islower() or c.isdigit() or c in "_-") for c in domain)
            or not s.database.enabled
            or not s.ingestion.synthetic_only
            or s.environment not in {"development", "integration"}
            or s.deployment_zone != "internal"
        ):
            raise IndexContractError("index_source_access_denied")
        async with self._db.transaction_async() as session:
            results = (
                await session.execute(
                    select(KnowledgeChunk, DocumentVersion, KnowledgeDocument, KnowledgeSource)
                    .join(
                        DocumentVersion,
                        and_(
                            KnowledgeChunk.version_id == DocumentVersion.id,
                            KnowledgeChunk.deployment_scope == DocumentVersion.deployment_scope,
                        ),
                    )
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
                        KnowledgeChunk.deployment_scope == "internal",
                        DocumentVersion.state == "awaiting_approval",
                        KnowledgeSource.owner_principal_id == principal_id,
                        KnowledgeSource.domain == domain,
                        KnowledgeSource.status == "active",
                        KnowledgeSource.classification == "synthetic_unclassified",
                        KnowledgeSource.policy_ref == "synthetic-only",
                    )
                    .order_by(KnowledgeChunk.ordinal)
                )
            ).all()
        if not 1 <= len(results) <= 32:
            raise IndexContractError("index_source_unavailable_or_out_of_bounds")
        checked = []
        seen: set[UUID] = set()
        document_id = results[0][2].id
        for ordinal, (chunk, version, doc, source) in enumerate(results):
            if (
                chunk.id in seen
                or doc.id != document_id
                or version.id != version_id
                or version.document_id != document_id
                or doc.source_id != source.id
                or chunk.ordinal != ordinal
                or not isinstance(chunk.canonical_text, str)
                or not isinstance(chunk.original_text, str)
                or not chunk.canonical_text.strip()
                or not isinstance(chunk.source_start, int)
                or not isinstance(chunk.source_end, int)
                or chunk.source_start < 0
                or chunk.source_end - chunk.source_start != len(chunk.original_text)
                or not isinstance(chunk.processor_version, str)
                or not isinstance(chunk.normalizer_version, str)
                or hashlib.sha256(chunk.canonical_text.encode("utf-8")).hexdigest() != chunk.checksum_sha256
            ):
                raise IndexContractError("invalid_pg_chunk_evidence")
            seen.add(chunk.id)
            checked.append(
                IndexSourceChunk(
                    id=chunk.id,
                    ordinal=chunk.ordinal,
                    canonical_text=chunk.canonical_text,
                    checksum_sha256=chunk.checksum_sha256,
                    processor_version=chunk.processor_version,
                    normalizer_version=chunk.normalizer_version,
                    page_number=chunk.page_number,
                    source_start=chunk.source_start,
                    source_end=chunk.source_end,
                )
            )
        return IndexSourceSnapshot(
            version_id=version_id,
            document_id=document_id,
            scope="internal",
            domain=domain,
            classification="synthetic_unclassified",
            chunks=tuple(checked),
        )
