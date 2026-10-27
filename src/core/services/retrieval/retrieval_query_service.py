"""Phase08 synthetic dense-candidate path with authoritative PostgreSQL recheck.

No HTTP endpoint, production answer, real query encoder, sparse strategy, or
Reranker is enabled by this initial slice; none may be inferred from its tests.
"""

from __future__ import annotations

import math
from uuid import UUID

from src.core.services.retrieval.retrieval_contract import CandidateHit, RetrievalContractError, fuse_rrf, normalize_query
from src.infrastructure.di.inject import inject
from src.infrastructure.providers.qdrant.qdrant_provider import QdrantProvider
from src.infrastructure.repositories.retrieval.retrieval_evidence_repository import (
    AuthorizedEvidence,
    RetrievalEvidenceRepository,
)
from src.infrastructure.utils.config_reader import ConfigReader


@inject
class RetrievalQueryService:
    def __init__(
        self,
        qdrant_provider: QdrantProvider,
        retrieval_evidence_repository: RetrievalEvidenceRepository,
        config_reader: ConfigReader,
    ):
        self._qdrant = qdrant_provider
        self._evidence = retrieval_evidence_repository
        self._settings = config_reader.settings

    async def retrieve_synthetic_dense_async(
        self,
        *,
        query: str,
        vector: list[float],
        principal_id: str,
        domain: str,
        allowed_document_ids: list[UUID],
        limit: int = 10,
        rank_constant: int = 60,
    ) -> list[AuthorizedEvidence]:
        """Development-only transport path, caller-provided synthetic vectors.

        The vector is never interpreted as an approved query-embedding model.
        Every selected result must survive a fresh PG/source/owner/state check.
        """
        normalize_query(query)
        cfg = self._settings
        if (
            cfg.environment not in {"development", "integration"}
            or not cfg.ingestion.synthetic_only
            or not cfg.qdrant.enabled
            or not cfg.database.enabled
            or cfg.deployment_zone != "internal"
            or not isinstance(allowed_document_ids, list)
            or not 1 <= len(allowed_document_ids) <= 1024
            or any(not isinstance(x, UUID) for x in allowed_document_ids)
            or len(set(allowed_document_ids)) != len(allowed_document_ids)
            or not isinstance(vector, list)
        ):
            raise RetrievalContractError("phase08_not_enabled")
        if not isinstance(principal_id, str) or not principal_id.strip() or len(principal_id) > 255:
            raise RetrievalContractError("invalid_principal")
        if not isinstance(domain, str) or not domain:
            raise RetrievalContractError("invalid_domain")
        # Phase04 provider enforces mandatory deployment/domain/classification/
        # document/published Qdrant filters before returning any candidates.
        results = await self._qdrant.search_async(
            vector,
            domain=domain,
            authorized_classifications=["synthetic_unclassified"],
            authorized_document_ids=allowed_document_ids,
            limit=limit,
        )
        dense = []
        for point in results:
            try:
                payload = point.payload
                if (
                    not isinstance(payload, dict)
                    or payload.get("published") is not True
                    or payload.get("deployment_scope") != cfg.deployment_zone
                    or payload.get("domain") != domain
                    or payload.get("classification") != "synthetic_unclassified"
                    or not isinstance(point.score, (int, float))
                    or not math.isfinite(point.score)
                ):
                    raise ValueError("invalid_payload")
                chunk_id = UUID(payload["chunk_id"])
                doc_id = UUID(payload["document_id"])
                version_id = UUID(payload["document_version_id"])
                if doc_id not in allowed_document_ids:
                    raise ValueError("unauthorized_document")
                dense.append(
                    CandidateHit(
                        chunk_id=chunk_id,
                        document_id=doc_id,
                        version_id=version_id,
                        score=float(point.score),
                    )
                )
            except (KeyError, ValueError, TypeError, AttributeError):
                # Do not return partially trusted evidence on malformed Qdrant
                # payloads; treat the whole candidate set as poisoned.
                raise RetrievalContractError("invalid_qdrant_candidate") from None
        candidates = fuse_rrf(dense, [], rank_constant=rank_constant, limit=limit)
        return await self._evidence.reauthorize_async(
            candidates=candidates,
            principal_id=principal_id,
            domain=domain,
            scope=cfg.deployment_zone,
        )
