"""PostgreSQL-only integration tests use disposable synthetic *_test databases."""

from __future__ import annotations

import asyncio
import os
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import StaleDataError

from src.core.services.conversation.conversation_service import ConversationService
from src.infrastructure.context.sql_db.psql_dbcontext import (
    Base,
    DatabaseUnavailable,
    PsqlDbContext,
    validate_database_url,
)
from src.infrastructure.di.bootstrap import bootstrap_di
from src.infrastructure.models.entities import (
    Conversation,
    DocumentVersion,
    KnowledgeChunk,
    KnowledgeDocument,
    KnowledgeSource,
    Message,
)
from src.infrastructure.models.ingestion import IngestionAuditEvent, IngestionJob
from src.infrastructure.repositories.base.base_repository import BaseRepository
from src.infrastructure.utils.config_reader import ConfigReader, ConfigurationError


def test_metadata_and_dependency_discovery(monkeypatch):
    monkeypatch.delenv("SCB_DATABASE_ENABLED", raising=False)
    container = bootstrap_di()
    assert container.resolve(ConfigReader).settings.database.enabled is False
    assert container.resolve(PsqlDbContext) is container.resolve(PsqlDbContext)
    assert set(Base.metadata.tables) == {
        "conversation",
        "message",
        "knowledge_source",
        "knowledge_document",
        "document_version",
        "knowledge_chunk",
        "ingestion_job",
        "ingestion_audit_event",
        "index_job",
        "index_manifest",
        "index_publication",
    }
    assert IngestionJob.__tablename__ == "ingestion_job"
    assert IngestionAuditEvent.__tablename__ == "ingestion_audit_event"
    assert len(Base.metadata.tables["message"].foreign_key_constraints) == 1
    assert Conversation.__mapper__.version_id_col is Conversation.__table__.c.revision


def test_database_settings_fail_closed_and_redact(monkeypatch):
    monkeypatch.setenv("SCB_ENV", "development")
    monkeypatch.setenv("SCB_DATABASE_ENABLED", "true")
    monkeypatch.setenv("SCB_DATABASE_URL", "sqlite:///topsecret")
    with pytest.raises(ConfigurationError) as exc:
        bootstrap_di().resolve(ConfigReader)
    assert "topsecret" not in str(exc.value)
    monkeypatch.setenv("SCB_DATABASE_ENABLED", "not-boolean")
    with pytest.raises(ConfigurationError):
        bootstrap_di().resolve(ConfigReader)


def test_database_url_validation_is_fail_closed_and_redacted():
    invalid_urls = (
        "not-a-database-url-topsecret",
        "postgresql+asyncpg://user:topsecret@127.0.0.1:bad/scb_phase03_test",
        "postgresql+asyncpg://user:topsecret@127.0.0.1/scb_phase03_test?ssl=disable",
    )
    for url in invalid_urls:
        with pytest.raises(DatabaseUnavailable) as exc:
            validate_database_url(url)
        assert "topsecret" not in str(exc.value)


def _test_url():
    url = os.environ.get("SCB_PHASE03_TEST_DATABASE_URL")
    if not url:
        pytest.skip("No isolated real PostgreSQL test database configured")
    from sqlalchemy.engine import make_url

    try:
        parsed = make_url(url)
        if (
            parsed.drivername != "postgresql+asyncpg"
            or not parsed.database
            or not parsed.database.endswith("_test")
            or parsed.host not in {"localhost", "127.0.0.1"}
        ):
            pytest.fail("Refusing PostgreSQL integration against non-disposable database")
    except ValueError:
        pytest.fail("Invalid isolated test database URL")
    return url


def test_real_postgresql_transactions_constraints_and_concurrency(monkeypatch):
    url = _test_url()
    monkeypatch.setenv("SCB_ENV", "development")
    monkeypatch.setenv("SCB_ZONE", "public")
    monkeypatch.setenv("SCB_DATABASE_ENABLED", "true")
    monkeypatch.setenv("SCB_DATABASE_URL", url)
    container = bootstrap_di()
    db = container.resolve(PsqlDbContext)
    service = container.resolve(ConversationService)

    async def exercise():
        await db.start_async()
        try:
            owner = "synthetic-" + str(uuid4())
            foreign_owner = "synthetic-" + str(uuid4())
            c = await service.create_async(owner, "public")
            assert await service.get_owned_async(c.id, foreign_owner, "public") is None
            with pytest.raises(PermissionError):
                await service.get_owned_async(c.id, owner, "internal")
            with pytest.raises(PermissionError):
                await service.create_async(owner, "internal")
            assert (await service.list_owned_async(owner, "public", limit=1))[0].id == c.id
            with pytest.raises(ValueError):
                await service.list_owned_async(owner, "public", limit=101)
            with pytest.raises(PermissionError):
                await service.append_message_async(c.id, foreign_owner, "public", "user", "forbidden")
            with pytest.raises(PermissionError):
                await service.append_message_async(c.id, owner, "internal", "user", "forbidden")
            repo = container.resolve(type(service._repository))
            with pytest.raises(PermissionError):
                await repo.get_by_id_async(c.id)
            first = await service.append_message_async(c.id, owner, "public", "user", "hello", "request-1")
            duplicate = await service.append_message_async(c.id, owner, "public", "user", "hello", "request-1")
            assert first.id == duplicate.id
            with pytest.raises(ValueError):
                await service.append_message_async(c.id, owner, "public", "user", "changed", "request-1")
            produced = await asyncio.gather(
                *(service.append_message_async(c.id, owner, "public", "assistant", f"reply-{i}") for i in range(4))
            )
            assert sorted(m.sequence_number for m in produced) == [2, 3, 4, 5]
            with pytest.raises(IntegrityError):
                async with db.transaction_async() as session:
                    session.add(
                        Message(
                            conversation_id=c.id,
                            deployment_scope="internal",
                            sequence_number=100,
                            role="user",
                            content="cross-scope",
                        )
                    )
                    await session.flush()
            with pytest.raises(IntegrityError):
                async with db.transaction_async() as session:
                    session.add(
                        Message(
                            conversation_id=c.id,
                            deployment_scope="public",
                            sequence_number=1,
                            role="user",
                            content="duplicate-seq",
                        )
                    )
                    await session.flush()
            aborted = Conversation(owner_principal_id=owner, deployment_scope="public")
            with pytest.raises(RuntimeError):
                async with db.transaction_async() as session:
                    session.add(aborted)
                    await session.flush()
                    raise RuntimeError("test rollback")
            assert await service.get_owned_async(aborted.id, owner, "public") is None
            async with db.session() as a, db.session() as b:
                left = await a.get(Conversation, c.id)
                right = await b.get(Conversation, c.id)
                left.status = "archived"
                await a.commit()
                with pytest.raises(PermissionError):
                    await service.append_message_async(c.id, owner, "public", "assistant", "after-archive")
                right.status = "archived"
                with pytest.raises(StaleDataError):
                    await b.commit()
                await b.rollback()
            generic = BaseRepository(db_context=db, model=KnowledgeSource)
            scratch = KnowledgeSource(owner_principal_id=owner, deployment_scope="public", domain="synthetic")
            assert await generic.insert_and_get_id_async(scratch) == scratch.id
            assert (await generic.get_by_id_async(scratch.id)).id == scratch.id
            assert any(item.id == scratch.id for item in await generic.get_all_async())
            scratch.domain = "synthetic-updated"
            assert (await generic.update_async(scratch)).domain == "synthetic-updated"
            assert await generic.delete_async(scratch.id) is True
            assert await generic.delete_async(scratch.id) is False
            aborted_source = KnowledgeSource(owner_principal_id=owner, deployment_scope="public", domain="rollback")
            with pytest.raises(RuntimeError):
                async with db.transaction_async() as session:
                    await generic.insert_async(aborted_source, session=session)
                    raise RuntimeError("rollback caller-owned session")
            assert await generic.get_by_id_async(aborted_source.id) is None
            source = KnowledgeSource(owner_principal_id=owner, deployment_scope="internal", domain="research")
            async with db.transaction_async() as session:
                session.add(source)
                await session.flush()
            with pytest.raises(IntegrityError):
                async with db.transaction_async() as session:
                    session.add(KnowledgeDocument(source_id=source.id, deployment_scope="public", title="isolated"))
                    await session.flush()
            doc = KnowledgeDocument(source_id=source.id, deployment_scope="internal", title="synthetic")
            async with db.transaction_async() as session:
                session.add(doc)
                await session.flush()
            version = DocumentVersion(
                document_id=doc.id, deployment_scope="internal", version_number=1, checksum_sha256="a" * 64
            )
            async with db.transaction_async() as session:
                session.add(version)
                await session.flush()
            with pytest.raises(IntegrityError):
                async with db.transaction_async() as session:
                    session.add(
                        DocumentVersion(
                            document_id=doc.id, deployment_scope="internal", version_number=1, checksum_sha256="b" * 64
                        )
                    )
                    await session.flush()
            chunk = KnowledgeChunk(
                version_id=version.id, deployment_scope="internal", ordinal=0, checksum_sha256="c" * 64
            )
            async with db.transaction_async() as session:
                session.add(chunk)
                await session.flush()
            with pytest.raises(IntegrityError):
                async with db.transaction_async() as session:
                    await session.delete(await session.get(KnowledgeSource, source.id))
                    await session.flush()
            async with db.transaction_async() as session:
                assert (await session.scalars(select(Message).where(Message.conversation_id == c.id))).all()
        finally:
            await db.close_async()

    asyncio.run(exercise())
