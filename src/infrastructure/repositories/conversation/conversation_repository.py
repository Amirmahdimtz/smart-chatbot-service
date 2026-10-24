"""Scoped conversation persistence; never use unscoped BaseRepository reads here."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.context.sql_db.psql_dbcontext import PsqlDbContext
from src.infrastructure.di.inject import inject
from src.infrastructure.models.entities import Conversation, Message
from src.infrastructure.repositories.base.base_repository import BaseRepository


@inject
class ConversationRepository(BaseRepository[Conversation]):
    def __init__(self, db_context: PsqlDbContext):
        super().__init__(db_context=db_context, model=Conversation)

    async def insert_async(self, entity, *, session: AsyncSession | None = None):
        raise PermissionError("Use scoped conversation creation")

    async def insert_and_get_id_async(self, entity, *, session: AsyncSession | None = None):
        raise PermissionError("Use scoped conversation creation")

    async def get_by_id_async(self, entity_id, *, session: AsyncSession | None = None):
        raise PermissionError("A principal and deployment scope are required")

    async def get_all_async(self, *, session: AsyncSession | None = None):
        raise PermissionError("A principal and deployment scope are required")

    async def update_async(self, entity, *, session: AsyncSession | None = None):
        raise PermissionError("A scoped mutation is required")

    async def delete_async(self, entity_id, *, session: AsyncSession | None = None):
        raise PermissionError("A scoped mutation is required")

    async def create_owned_async(self, principal: str, scope: str) -> Conversation:
        return await super().insert_async(Conversation(owner_principal_id=principal, deployment_scope=scope))

    async def get_owned_async(self, entity_id: UUID, principal: str, scope: str) -> Conversation | None:
        async with self._db.transaction_async() as session:
            return await session.scalar(
                select(Conversation).where(
                    Conversation.id == entity_id,
                    Conversation.owner_principal_id == principal,
                    Conversation.deployment_scope == scope,
                )
            )

    async def list_owned_async(
        self, principal: str, scope: str, *, limit: int = 50, offset: int = 0
    ) -> list[Conversation]:
        if not 1 <= limit <= 100 or not 0 <= offset <= 10000:
            raise ValueError("Invalid pagination")
        async with self._db.transaction_async() as session:
            result = await session.scalars(
                select(Conversation)
                .where(Conversation.owner_principal_id == principal, Conversation.deployment_scope == scope)
                .order_by(Conversation.created_at, Conversation.id)
                .limit(limit)
                .offset(offset)
            )
            return list(result.all())

    async def append_owned_message_async(
        self,
        conversation_id: UUID,
        principal: str,
        scope: str,
        role: str,
        content: str,
        idempotency_key: str | None = None,
    ) -> Message:
        async with self._db.transaction_async() as session:
            conversation = await session.scalar(
                select(Conversation)
                .where(
                    Conversation.id == conversation_id,
                    Conversation.owner_principal_id == principal,
                    Conversation.deployment_scope == scope,
                    Conversation.status == "active",
                )
                .with_for_update()
            )
            if conversation is None:
                raise PermissionError("Conversation unavailable")
            if idempotency_key is not None:
                prior = await session.scalar(
                    select(Message).where(
                        Message.conversation_id == conversation_id,
                        Message.idempotency_key == idempotency_key,
                    )
                )
                if prior is not None:
                    if prior.content != content or prior.role != role:
                        raise ValueError("Idempotency key reuse with a different payload")
                    return prior
            maximum = await session.scalar(
                select(func.coalesce(func.max(Message.sequence_number), 0)).where(
                    Message.conversation_id == conversation_id
                )
            )
            message = Message(
                conversation_id=conversation_id,
                deployment_scope=scope,
                sequence_number=maximum + 1,
                role=role,
                content=content,
                idempotency_key=idempotency_key,
            )
            session.add(message)
            conversation.updated_at = func.now()
            await session.flush()
            await session.refresh(message)
            return message
