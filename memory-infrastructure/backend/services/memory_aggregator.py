from __future__ import annotations

import time
from datetime import datetime, timezone
from uuid import uuid4

from models import IngestRequest, IngestResponse
from .memory_store import MemoryStore, MemoryRecord
from .memory_index import MemoryIndexService
from .memory_compounding import MemoryCompoundingService
from .utils import estimate_token_count


class MemoryAggregator:
    def __init__(
        self,
        store: MemoryStore,
        indexer: MemoryIndexService,
        compounding: MemoryCompoundingService,
    ) -> None:
        self.store = store
        self.indexer = indexer
        self.compounding = compounding

    async def ingest(self, user_id: str, request: IngestRequest) -> IngestResponse:
        start = time.time()
        entry_id = str(uuid4())
        metadata = {
            "type": request.content_type,
            "title": request.title,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        if request.metadata:
            metadata.update(request.metadata)
        index_result = await self.indexer.index_text_content(
            user_id=user_id,
            doc_id=entry_id,
            content=request.content,
            metadata=metadata,
        )

        preview = request.content[:500]
        token_count = estimate_token_count(request.content)

        record = MemoryRecord(
            id=index_result.doc_id,
            user_id=user_id,
            content_type=request.content_type,
            title=request.title,
            content_preview=preview,
            content=request.content,
            embedding_id=index_result.embedding_id,
            indexed_at=index_result.indexed_at,
            last_accessed_at=None,
            access_count=0,
            relevance_decay=1.0,
            source_url=request.source_url,
            source_metadata=request.metadata,
            related_entries=[],
            tags=request.tags,
            token_count=token_count,
        )
        await self.store.upsert(record)

        compounding_result = await self.compounding.on_content_added(
            user_id=user_id,
            entry_id=record.id,
            content=request.content,
            content_type=request.content_type,
        )

        processing_time_ms = int((time.time() - start) * 1000)
        return IngestResponse(
            entry_id=record.id,
            indexed=True,
            embedding_id=record.embedding_id,
            token_count=token_count,
            related_entries=self.compounding.related_entries_cache.get(record.id, []),
            processing_time_ms=processing_time_ms,
        )

    async def ingest_bulk(self, user_id: str, entries: list[IngestRequest]) -> tuple[list[IngestResponse], list[dict]]:
        successful: list[IngestResponse] = []
        failed: list[dict] = []
        for idx, entry in enumerate(entries):
            try:
                response = await self.ingest(user_id, entry)
                successful.append(response)
            except Exception as exc:
                failed.append({"index": idx, "error": str(exc)})
        return successful, failed
