"""Phase 05 validation and injectable ingestion service contract."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from uuid import uuid4

import pytest

from src.core.services.ingestion.ingestion_service import IngestionService
from src.infrastructure.di.bootstrap import bootstrap_di
from src.infrastructure.repositories.ingestion.ingestion_job_repository import IngestionJobRepository


class RejectingRepository:
    async def enqueue_owned_async(self, **kwargs):
        raise AssertionError("Invalid input reached repository")

    async def claim_next_async(self, **kwargs):
        raise AssertionError("Invalid input reached repository")


def test_ingestion_di_and_guarded_generic_crud():
    container = bootstrap_di()
    repo = container.resolve(IngestionJobRepository)
    assert container.resolve(IngestionService)._jobs.__class__ is IngestionJobRepository

    async def exercise():
        with pytest.raises(PermissionError):
            await repo.get_all_async()
        with pytest.raises(PermissionError):
            await repo.get_by_id_async(uuid4())
        with pytest.raises(PermissionError):
            await repo.delete_async(uuid4())

    asyncio.run(exercise())


def test_phase05_fail_closed_validation():
    service = IngestionService(RejectingRepository(), SimpleNamespace(settings=SimpleNamespace(deployment_zone="public")))
    source_id, version_id = uuid4(), uuid4()

    async def exercise():
        base = dict(
            principal="synthetic-owner", scope="public", source_id=source_id,
            version_id=version_id, idempotency_key="key", max_attempts=2,
        )
        for change, error in [
            ({"scope": "internal"}, PermissionError),
            ({"principal": "  "}, ValueError),
            ({"source_id": "not-uuid"}, ValueError),
            ({"idempotency_key": ""}, ValueError),
            ({"max_attempts": 21}, ValueError),
            ({"max_attempts": True}, ValueError),
        ]:
            with pytest.raises(error):
                await service.enqueue_async(**(base | change))
        with pytest.raises(PermissionError):
            await service.claim_next_async(scope="internal", worker_id="worker-1")
        with pytest.raises(ValueError):
            await service.claim_next_async(scope="public", worker_id="../worker")
        with pytest.raises(ValueError):
            await service.claim_next_async(scope="public", worker_id="worker-1", lease_seconds=0)
        with pytest.raises(ValueError):
            await service.fail_async(
                scope="public", job_id=uuid4(), lease_token=uuid4(), error_code="Exception: private data"
            )

    asyncio.run(exercise())
