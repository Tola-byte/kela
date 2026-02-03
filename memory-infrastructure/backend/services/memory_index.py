from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .embedding import LocalVoyageClient
from .vector_store import LocalVectorStore


@dataclass
class IndexResult:
    doc_id: str
    embedding_id: str
    indexed_at: datetime
    token_count: int


class MemoryIndexService:
    def __init__(self, vector_store: LocalVectorStore, embedding_client: LocalVoyageClient) -> None:
        self.vector_store = vector_store
        self.embedding_client = embedding_client

    async def index_text_content(
        self,
        user_id: str,
        doc_id: str | None,
        content: str,
        metadata: dict[str, Any],
    ) -> IndexResult:
        embedding = await self.embedding_client.embed(content)
        entry_id = doc_id or str(uuid4())
        await self.vector_store.upsert(
            user_id=user_id,
            doc_id=entry_id,
            vector=embedding,
            payload=metadata,
        )
        return IndexResult(
            doc_id=entry_id,
            embedding_id=entry_id,
            indexed_at=datetime.now(timezone.utc),
            token_count=max(1, len(content) // 4),
        )

    async def delete_indexed_content(self, user_id: str, doc_id: str) -> bool:
        return await self.vector_store.delete(user_id, doc_id)
