"""Internal conversation workflow; not exposed over HTTP until identity/policy approval."""

from __future__ import annotations

from uuid import UUID

from src.infrastructure.di.inject import inject
from src.infrastructure.models.entities import Conversation, Message
from src.infrastructure.repositories.conversation.conversation_repository import ConversationRepository


@inject
class ConversationService:
    def __init__(self, conversation_repository: ConversationRepository):
        self._repository = conversation_repository

    @staticmethod
    def _identity(principal: str, scope: str) -> tuple[str, str]:
        if not isinstance(principal, str) or not principal.strip() or len(principal) > 255:
            raise ValueError("Invalid principal")
        if scope not in {"public", "internal"}:
            raise ValueError("Invalid deployment scope")
        return principal, scope

    async def create_async(self, principal: str, scope: str) -> Conversation:
        principal, scope = self._identity(principal, scope)
        return await self._repository.create_owned_async(principal, scope)

    async def get_owned_async(self, conversation_id: UUID, principal: str, scope: str) -> Conversation | None:
        principal, scope = self._identity(principal, scope)
        return await self._repository.get_owned_async(conversation_id, principal, scope)

    async def list_owned_async(
        self, principal: str, scope: str, *, limit: int = 50, offset: int = 0
    ) -> list[Conversation]:
        principal, scope = self._identity(principal, scope)
        return await self._repository.list_owned_async(principal, scope, limit=limit, offset=offset)

    async def append_message_async(
        self,
        conversation_id: UUID,
        principal: str,
        scope: str,
        role: str,
        content: str,
        idempotency_key: str | None = None,
    ) -> Message:
        principal, scope = self._identity(principal, scope)
        if role not in {"user", "assistant"} or not isinstance(content, str) or not 1 <= len(content) <= 100000:
            raise ValueError("Invalid message")
        if idempotency_key is not None and (
            not isinstance(idempotency_key, str) or not 1 <= len(idempotency_key) <= 128
        ):
            raise ValueError("Invalid idempotency key")
        return await self._repository.append_owned_message_async(
            conversation_id, principal, scope, role, content, idempotency_key
        )
