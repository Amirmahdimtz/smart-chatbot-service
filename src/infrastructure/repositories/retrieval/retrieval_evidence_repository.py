"""PostgreSQL is authoritative over any untrusted Qdrant retrieval candidates.

Synthetic-only owner authorization until organization policy D-07/D-08 and
Phase07 publication manifests are approved. No alternate public read path.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import and_, select

from src.core.services.retrieval.retrieval_contract import FusedCandidate, RetrievalContractError
from src.infrastructure.context.sql_db.psql_dbcontext import PsqlDbContext
from src.infrastructure.di.inject import inject
from src.infrastructure.models.entities import DocumentVersion, KnowledgeChunk, KnowledgeDocument, KnowledgeSource
from src.infrastructure.utils.config_reader import ConfigReader


@dataclass(frozen=True)
class AuthorizedEvidence:
    chunk_id: UUID
    document_id: UUID
    version_id: UUID
    canonical: str
    original: str
    page: int | None
    source_start: int
    source_end: int
    section: str | None
    score: float


@inject
class RetrievalEvidenceRepository:
    def __init__(self, db_context: PsqlDbContext, config_reader: ConfigReader):
        self._db = db_context
        self._settings = config_reader.settings

    async def reauthorize_async(
        self,
        *,
        candidates: list[FusedCandidate],
        principal_id: str,
        domain: str,
        scope: str,
    ) -> list[AuthorizedEvidence]:
        """Fail closed on revoked/unapproved/superseded versions and foreign owners.

        This read never grants publication: an isolated Phase07 publication gate
        must first set authoritative visible state. No direct public API exists.
        """
        if (
            not self._settings.database.enabled
            or not self._settings.ingestion.synthetic_only
            or self._settings.environment not in {"development", "integration"}
            or scope != self._settings.deployment_zone
            or not isinstance(principal_id, str)
            or not 1 <= len(principal_id) <= 255
            or not isinstance(domain, str)
            or not 1 <= len(domain) <= 64
            or not all(c.isascii() and (c.islower() or c.isdigit() or c in "_-") for c in domain)
            or not isinstance(candidates, list)
            or len(candidates) > 100
            or any(not isinstance(c, FusedCandidate) for c in candidates)
        ):
            raise RetrievalContractError("unauthorized_retrieval_scope")
        if not candidates:
            return []
        if len({v.chunk_id for v in candidates}) != len(candidates):
            raise RetrievalContractError("duplicate_candidates")
        async with self._db.transaction_async() as session:
            rows = await session.execute(
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
                    KnowledgeChunk.id.in_([v.chunk_id for v in candidates]),
                    KnowledgeChunk.deployment_scope == scope,
                    DocumentVersion.state == "published",
                    KnowledgeSource.status == "active",
                    KnowledgeSource.owner_principal_id == principal_id,
                    KnowledgeSource.domain == domain,
                    KnowledgeSource.classification == "synthetic_unclassified",
                    KnowledgeSource.policy_ref == "synthetic-only",
                )
            )
            found: dict[UUID, tuple[KnowledgeChunk, DocumentVersion, KnowledgeDocument]] = {}
            for chunk, version, document, _source in rows:
                found[chunk.id] = (chunk, version, document)
        authorized = []
        for candidate in candidates:
            entry = found.get(candidate.chunk_id)
            if entry is None:
                continue
            chunk, version, document = entry
            if (
                version.id != candidate.version_id
                or document.id != candidate.document_id
                or not isinstance(chunk.original_text, str)
                or not isinstance(chunk.canonical_text, str)
                or not chunk.canonical_text.strip()
                or chunk.source_start is None
                or chunk.source_end is None
                or chunk.source_start < 0
                or chunk.source_end <= chunk.source_start
                or (chunk.page_number is not None and chunk.page_number < 1)
                or hashlib.sha256(chunk.canonical_text.encode("utf-8")).hexdigest() != chunk.checksum_sha256
            ):
                continue
            authorized.append(
                AuthorizedEvidence(
                    chunk_id=chunk.id,
                    document_id=document.id,
                    version_id=version.id,
                    canonical=chunk.canonical_text,
                    original=chunk.original_text,
                    page=chunk.page_number,
                    source_start=chunk.source_start,
                    source_end=chunk.source_end,
                    section=chunk.section_title,
                    score=candidate.rrf_score,
                )
            )
        return authorized
