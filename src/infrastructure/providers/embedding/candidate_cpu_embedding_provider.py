"""Phase07 genuine local CPU embedding of synthetic data; an UNAPPROVED D-03 candidate.

Pinned public safetensors, local inference only. No Cloud API, no production
API, no auto-publication and no per-request model loading.
"""

from __future__ import annotations

import asyncio
import math
from collections.abc import Sequence

from src.core.services.indexing.index_manifest import IndexContractError
from src.infrastructure.utils.config_reader import ConfigReader


class CandidateModelUnavailable(RuntimeError):
    def __init__(self):
        super().__init__("candidate_embedding_unavailable")


class CandidateCpuEmbeddingProvider:
    """Bounded single-owner warm model, used only in synthetic Development CI."""

    MODEL_REVISIONS = {
        "e5-small": (
            "intfloat/multilingual-e5-small",
            "614241f622f53c4eeff9890bdc4f31cfecc418b3",
            "query: ",
            "passage: ",
        ),
        "minilm-l12": (
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            "e8f8c211226b894fcb81acc59f3b34ba3efd5f42",
            "",
            "",
        ),
    }
    DIMENSION = 384

    def __init__(self, config_reader: ConfigReader, *, candidate: str):
        cfg = config_reader.settings
        if (
            candidate not in self.MODEL_REVISIONS
            or cfg.environment not in {"development", "integration"}
            or cfg.deployment_zone != "internal"
            or not cfg.ingestion.synthetic_only
            or not cfg.database.enabled
            or not cfg.qdrant.enabled
            or cfg.qdrant.dimension != self.DIMENSION
            or cfg.qdrant.distance != "Cosine"
        ):
            raise IndexContractError("candidate_embedding_not_authorized")
        self._candidate = candidate
        self._model = None
        self._gate = asyncio.Semaphore(1)
        self._initialization = asyncio.Lock()
        self.load_count = 0

    @property
    def model_id(self) -> str:
        # Stable manifest-safe identifier; full Hub identity in provider spec.
        return "e5_small" if self._candidate == "e5-small" else "minilm_l12"

    @property
    def revision(self) -> str:
        return self.MODEL_REVISIONS[self._candidate][1]

    async def start_async(self) -> None:
        async with self._initialization:
            if self._model is not None:
                return
            try:
                from sentence_transformers import SentenceTransformer

                hub_id, revision, _, _ = self.MODEL_REVISIONS[self._candidate]
                model = await asyncio.to_thread(
                    SentenceTransformer,
                    hub_id,
                    revision=revision,
                    device="cpu",
                    trust_remote_code=False,
                    model_kwargs={"use_safetensors": True},
                )
                model.max_seq_length = min(model.max_seq_length, 128)
                if model.get_sentence_embedding_dimension() != self.DIMENSION:
                    raise ValueError("dimension")
                self._model = model
                self.load_count += 1
                await self._embed_locked(["warmup"], "passage", 1)
            except Exception:
                self._model = None
                raise CandidateModelUnavailable() from None

    async def _embed_locked(self, texts: Sequence[str], kind: str, batch_size: int) -> list[list[float]]:
        if self._model is None:
            raise CandidateModelUnavailable()
        _, _, query_prefix, passage_prefix = self.MODEL_REVISIONS[self._candidate]
        prefix = query_prefix if kind == "query" else passage_prefix
        try:
            arr = await asyncio.to_thread(
                self._model.encode,
                [prefix + value for value in texts],
                batch_size=batch_size,
                normalize_embeddings=True,
                convert_to_numpy=True,
                show_progress_bar=False,
            )
            vectors = arr.tolist()
            if len(vectors) != len(texts) or any(
                not isinstance(v, list)
                or len(v) != self.DIMENSION
                or not all(isinstance(x, (int, float)) and math.isfinite(x) for x in v)
                or not any(x != 0 for x in v)
                for v in vectors
            ):
                raise ValueError("bad_model_vector")
            return vectors
        except Exception:
            raise CandidateModelUnavailable() from None

    async def embed_async(self, texts: Sequence[str], *, kind: str, batch_size: int = 4) -> list[list[float]]:
        if (
            kind not in {"query", "passage"}
            or isinstance(texts, (str, bytes))
            or not isinstance(texts, (list, tuple))
            or not 1 <= len(texts) <= 32
            or not isinstance(batch_size, int)
            or not 1 <= batch_size <= 8
            or any(not isinstance(t, str) or not t.strip() or len(t) > 4000 for t in texts)
        ):
            raise IndexContractError("invalid_candidate_embedding_request")
        if self._model is None:
            raise CandidateModelUnavailable()
        async with self._gate:
            return await self._embed_locked(texts, kind, batch_size)

    async def close_async(self) -> None:
        async with self._gate:
            self._model = None
