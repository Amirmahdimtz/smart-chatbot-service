"""Phase 04: scoped, async Qdrant infrastructure; not an authorization authority."""

from __future__ import annotations

import asyncio
import math
from collections.abc import Sequence
from dataclasses import dataclass
from uuid import NAMESPACE_URL, UUID, uuid5

import httpx
from qdrant_client import AsyncQdrantClient, models
from qdrant_client.http.exceptions import ResponseHandlingException, UnexpectedResponse

from src.infrastructure.context.vault.vault_service import VaultService
from src.infrastructure.di.inject import inject
from src.infrastructure.utils.config_reader import ConfigReader, QdrantSettings


class QdrantUnavailable(RuntimeError):
    def __init__(self):
        super().__init__("Vector service unavailable or incorrectly configured")


class QdrantContractError(ValueError):
    def __init__(self):
        super().__init__("Invalid vector or scoped query contract")


@dataclass(frozen=True)
class QdrantBackupManifest:
    """Sidecar backup metadata. Not the Phase 07 authoritative index manifest."""

    collection_name: str
    snapshot_name: str
    schema_version: int
    dimension: int
    distance: str
    deployment_zone: str
    active_alias_target: str | None


@dataclass(frozen=True)
class VectorRecord:
    chunk_id: UUID
    document_id: UUID
    document_version_id: UUID
    domain: str
    classification: str
    vector: Sequence[float]
    published: bool = False


def deterministic_point_id(record: VectorRecord, schema_version: int) -> str:
    return str(uuid5(NAMESPACE_URL, f"scb:{record.chunk_id}:{record.document_version_id}:{schema_version}"))


def _safe_token(value: str) -> bool:
    return (
        isinstance(value, str)
        and 0 < len(value) <= 100
        and all(char.isascii() and (char.islower() or char.isdigit() or char in "_-") for char in value)
    )


@inject
class QdrantProvider:
    """One client per application, with explicit lifecycle and no HTTP exposure."""

    __di_singleton__ = True

    def __init__(self, config_reader: ConfigReader, vault_service: VaultService):
        self._cfg: QdrantSettings = config_reader.settings.qdrant
        self._zone = config_reader.settings.deployment_zone
        self._vault = vault_service
        self._client: AsyncQdrantClient | None = None

    @property
    def collection_name(self) -> str:
        return f"{self._cfg.collection_prefix}_{self._zone}_v{self._cfg.schema_version}"

    @property
    def alias_name(self) -> str:
        return f"{self._cfg.collection_prefix}_{self._zone}_active"

    async def start_async(self) -> None:
        if not self._cfg.enabled:
            return
        if self._client is not None:
            return
        key = self._cfg.api_key
        if self._cfg.vault_secret_path:
            try:
                secret = await self._vault.read_secret_async(self._cfg.vault_secret_path)
                key = secret.get("api_key")
            except Exception:
                raise QdrantUnavailable() from None
        if not isinstance(key, str) or not key:
            raise QdrantUnavailable()
        client = None
        try:
            client = AsyncQdrantClient(
                url=self._cfg.url,
                api_key=key,
                timeout=self._cfg.timeout_seconds,
                check_compatibility=False,
            )
            await client.get_collections()
        except Exception:
            if client is not None:
                await client.close()
            raise QdrantUnavailable() from None
        self._client = client

    async def close_async(self) -> None:
        client, self._client = self._client, None
        if client is not None:
            await client.close()

    def _ready(self) -> AsyncQdrantClient:
        if not self._cfg.enabled or self._client is None:
            raise QdrantUnavailable()
        return self._client

    async def _call_async(self, method: str, *, allow_not_found: bool = False, allow_conflict: bool = False, **kwargs):
        client = self._ready()
        for attempt in range(self._cfg.max_retries + 1):
            try:
                return await getattr(client, method)(**kwargs)
            except UnexpectedResponse as exc:
                if allow_not_found and exc.status_code == 404:
                    return None
                if allow_conflict and exc.status_code == 409:
                    return False
                if exc.status_code not in {429, 500, 502, 503, 504} or attempt == self._cfg.max_retries:
                    raise QdrantUnavailable() from None
            except (ResponseHandlingException, httpx.TransportError, TimeoutError, ConnectionError):
                if attempt == self._cfg.max_retries:
                    raise QdrantUnavailable() from None
            if attempt < self._cfg.max_retries:
                await asyncio.sleep(min(0.1 * (2**attempt), 0.5))
        raise QdrantUnavailable()

    async def check_async(self) -> bool:
        await self._call_async("get_collections")
        return True

    async def ensure_collection_async(self) -> str:
        """Non-destructive: fail on incompatible schema instead of changing it in place."""
        name = self.collection_name
        # Probe once. Only HTTP 404 may mean the collection is absent;
        # auth/network/timeout failures must never trigger provisioning.
        info = await self._call_async("get_collection", collection_name=name, allow_not_found=True)
        if info is None:
            # Concurrent workers may create the same collection. A 409 is safe
            # only after re-reading and validating the resulting schema below.
            await self._call_async(
                "create_collection",
                collection_name=name,
                vectors_config=models.VectorParams(
                    size=self._cfg.dimension, distance=models.Distance(self._cfg.distance)
                ),
                allow_conflict=True,
            )
            info = await self._call_async("get_collection", collection_name=name)
        vectors = info.config.params.vectors
        if (
            not isinstance(vectors, models.VectorParams)
            or vectors.size != self._cfg.dimension
            or vectors.distance != models.Distance(self._cfg.distance)
        ):
            raise QdrantContractError()
        indexes = {
            "deployment_scope": models.PayloadSchemaType.KEYWORD,
            "document_id": models.PayloadSchemaType.KEYWORD,
            "domain": models.PayloadSchemaType.KEYWORD,
            "classification": models.PayloadSchemaType.KEYWORD,
            "published": models.PayloadSchemaType.BOOL,
        }
        for field, schema in indexes.items():
            existing_index = info.payload_schema.get(field)
            if existing_index is not None:
                if existing_index.data_type != schema:
                    raise QdrantContractError()
                continue
            await self._call_async(
                "create_payload_index",
                collection_name=name,
                field_name=field,
                field_schema=schema,
                wait=True,
            )
        return name

    async def activate_collection_async(self) -> None:
        """Atomic alias cutover. Caller must explicitly authorize an index migration."""
        name = await self.ensure_collection_async()
        current = await self._call_async("get_aliases")
        existing = next((a for a in current.aliases if a.alias_name == self.alias_name), None)
        if existing and existing.collection_name == name:
            return
        if existing and not existing.collection_name.startswith(f"{self._cfg.collection_prefix}_{self._zone}_v"):
            raise QdrantContractError()
        operations = []
        if existing:
            operations.append(models.DeleteAliasOperation(delete_alias=models.DeleteAlias(alias_name=self.alias_name)))
        operations.append(
            models.CreateAliasOperation(
                create_alias=models.CreateAlias(collection_name=name, alias_name=self.alias_name)
            )
        )
        await self._call_async("update_collection_aliases", change_aliases_operations=operations)

    def _vector(self, values: Sequence[float]) -> list[float]:
        try:
            valid_size = len(values) == self._cfg.dimension
        except (TypeError, ValueError):
            raise QdrantContractError() from None
        if not valid_size:
            raise QdrantContractError()
        try:
            output = [float(v) for v in values]
        except (TypeError, ValueError, OverflowError):
            raise QdrantContractError() from None
        if not all(math.isfinite(v) for v in output):
            raise QdrantContractError()
        return output

    async def upsert_async(self, records: Sequence[VectorRecord]) -> list[str]:
        if not records or len(records) > self._cfg.batch_size:
            raise QdrantContractError()
        points = []
        point_ids: list[str] = []
        seen: set[str] = set()
        for record in records:
            if (
                not isinstance(record, VectorRecord)
                or not all(
                    isinstance(v, UUID) for v in (record.chunk_id, record.document_id, record.document_version_id)
                )
                or not _safe_token(record.domain)
                or not _safe_token(record.classification)
                or not isinstance(record.published, bool)
            ):
                raise QdrantContractError()
            point_id = deterministic_point_id(record, self._cfg.schema_version)
            if point_id in seen:
                raise QdrantContractError()
            seen.add(point_id)
            point_ids.append(point_id)
            points.append(
                models.PointStruct(
                    id=point_id,
                    vector=self._vector(record.vector),
                    payload={
                        "chunk_id": str(record.chunk_id),
                        "document_id": str(record.document_id),
                        "document_version_id": str(record.document_version_id),
                        "deployment_scope": self._zone,
                        "domain": record.domain,
                        "classification": record.classification,
                        "published": bool(record.published),
                        "index_version": self._cfg.schema_version,
                    },
                )
            )
        result = await self._call_async("upsert", collection_name=self.collection_name, points=points, wait=True)
        if result.status != models.UpdateStatus.COMPLETED:
            raise QdrantUnavailable()
        return point_ids

    def _filter(self, domain: str, classifications: Sequence[str], document_ids: Sequence[UUID]) -> models.Filter:
        if (
            not _safe_token(domain)
            or not classifications
            or isinstance(classifications, (str, bytes))
            or not document_ids
            or isinstance(document_ids, (str, bytes))
            or len(document_ids) > 1024
            or any(not _safe_token(v) for v in classifications)
            or any(not isinstance(v, UUID) for v in document_ids)
        ):
            raise QdrantContractError()
        return models.Filter(
            must=[
                models.FieldCondition(key="deployment_scope", match=models.MatchValue(value=self._zone)),
                models.FieldCondition(key="domain", match=models.MatchValue(value=domain)),
                models.FieldCondition(key="classification", match=models.MatchAny(any=list(classifications))),
                models.FieldCondition(key="document_id", match=models.MatchAny(any=[str(v) for v in document_ids])),
                models.FieldCondition(key="published", match=models.MatchValue(value=True)),
            ]
        )

    async def search_async(
        self,
        vector: Sequence[float],
        *,
        domain: str,
        authorized_classifications: Sequence[str],
        authorized_document_ids: Sequence[UUID],
        limit: int = 10,
    ) -> list[models.ScoredPoint]:
        """Candidate lookup only; Core must re-authorize each result against PostgreSQL."""
        if not 1 <= limit <= 100:
            raise QdrantContractError()
        scoped = self._filter(domain, authorized_classifications, authorized_document_ids)
        response = await self._call_async(
            "query_points",
            collection_name=self.alias_name,
            query=self._vector(vector),
            query_filter=scoped,
            limit=limit,
            with_payload=True,
            with_vectors=False,
        )
        return response.points

    async def delete_document_points_async(self, document_id: UUID, *, domain: str) -> None:
        if not isinstance(document_id, UUID) or not _safe_token(domain):
            raise QdrantContractError()
        scoped = models.Filter(
            must=[
                models.FieldCondition(key="deployment_scope", match=models.MatchValue(value=self._zone)),
                models.FieldCondition(key="domain", match=models.MatchValue(value=domain)),
                models.FieldCondition(key="document_id", match=models.MatchValue(value=str(document_id))),
            ]
        )
        result = await self._call_async(
            "delete",
            collection_name=self.collection_name,
            points_selector=models.FilterSelector(filter=scoped),
            wait=True,
        )
        if result.status != models.UpdateStatus.COMPLETED:
            raise QdrantUnavailable()

    async def snapshot_async(self) -> str:
        """Create, never restore, a snapshot; restore is an explicit isolated-ops drill."""
        snapshot = await self._call_async("create_snapshot", collection_name=self.collection_name)
        if not isinstance(snapshot.name, str) or not snapshot.name.endswith(".snapshot"):
            raise QdrantUnavailable()
        return snapshot.name

    async def backup_manifest_async(self) -> QdrantBackupManifest:
        """Capture snapshot and its version/alias sidecar; restore remains a separate operation."""
        name = self.collection_name
        info = await self._call_async("get_collection", collection_name=name)
        params = info.config.params.vectors
        if (
            not isinstance(params, models.VectorParams)
            or params.size != self._cfg.dimension
            or params.distance != models.Distance(self._cfg.distance)
        ):
            raise QdrantContractError()
        before = await self._call_async("get_aliases")
        target = next((a.collection_name for a in before.aliases if a.alias_name == self.alias_name), None)
        snapshot_name = await self.snapshot_async()
        after = await self._call_async("get_aliases")
        latest = next((a.collection_name for a in after.aliases if a.alias_name == self.alias_name), None)
        if target != latest:
            raise QdrantUnavailable()
        return QdrantBackupManifest(
            collection_name=name,
            snapshot_name=snapshot_name,
            schema_version=self._cfg.schema_version,
            dimension=params.size,
            distance=params.distance.value,
            deployment_zone=self._zone,
            active_alias_target=target,
        )

