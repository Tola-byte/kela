from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, HTTPException, Query, status

from models import (
    BulkIngestRequest,
    BulkIngestResponse,
    IngestRequest,
    IngestResponse,
    MemoryEntry,
    MemoryHealthReport,
    MemoryStats,
)
from services.app_services import memory_aggregator, memory_stats, compounding_service
from services.factory import factory
from services.utils import now_utc

router = APIRouter(prefix="/api/memory", tags=["memory"])


@router.get("/stats", response_model=MemoryStats)
async def get_memory_stats(
    user_id: str = Query(..., min_length=1),
) -> MemoryStats:
    profile = await factory.voice_profile_service.get_profile(user_id)
    events = await factory.memory_store.get_compounding_events(user_id, 1)
    last_compounding = events[0]["timestamp"] if events else None
    return await memory_stats.get_stats(user_id, profile.confidence if profile else 0.0, last_compounding)


@router.get("/health", response_model=MemoryHealthReport)
async def get_memory_health(
    user_id: str = Query(..., min_length=1),
) -> MemoryHealthReport:
    profile = await factory.voice_profile_service.get_profile(user_id)
    events = await factory.memory_store.get_compounding_events(user_id, 1)
    last_compounding = events[0]["timestamp"] if events else None
    return await memory_stats.get_health_report(
        user_id, profile.confidence if profile else 0.0, last_compounding
    )


@router.get("/entries", response_model=list[MemoryEntry])
async def list_memory_entries(
    user_id: str = Query(..., min_length=1),
    content_type: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("indexed_at"),
) -> list[MemoryEntry]:
    records = await factory.memory_store.list(user_id, content_type, limit, offset, sort_by)
    return [
        MemoryEntry(
            id=record.id,
            user_id=record.user_id,
            content_type=record.content_type,
            title=record.title,
            content_preview=record.content_preview,
            embedding_id=record.embedding_id,
            indexed_at=record.indexed_at,
            last_accessed_at=record.last_accessed_at,
            access_count=record.access_count,
            relevance_decay=record.relevance_decay,
            source_url=record.source_url,
            source_metadata=record.source_metadata,
            related_entries=record.related_entries,
            tags=record.tags,
        )
        for record in records
    ]


@router.get("/entries/{entry_id}", response_model=MemoryEntry)
async def get_memory_entry(
    entry_id: str,
    user_id: str = Query(..., min_length=1),
) -> MemoryEntry:
    record = await factory.memory_store.get(user_id, entry_id)
    if not record:
        raise HTTPException(status_code=404, detail="Entry not found")
    await compounding_service.on_content_accessed(user_id, entry_id)
    return MemoryEntry(
        id=record.id,
        user_id=record.user_id,
        content_type=record.content_type,
        title=record.title,
        content_preview=record.content_preview,
        embedding_id=record.embedding_id,
        indexed_at=record.indexed_at,
        last_accessed_at=record.last_accessed_at,
        access_count=record.access_count,
        relevance_decay=record.relevance_decay,
        source_url=record.source_url,
        source_metadata=record.source_metadata,
        related_entries=record.related_entries,
        tags=record.tags,
    )


@router.post("/ingest", response_model=IngestResponse, status_code=status.HTTP_201_CREATED)
async def ingest_content(
    request: IngestRequest,
    user_id: str = Query(..., min_length=1),
) -> IngestResponse:
    return await memory_aggregator.ingest(user_id, request)


@router.post("/ingest/bulk", response_model=BulkIngestResponse, status_code=status.HTTP_201_CREATED)
async def bulk_ingest_content(
    request: BulkIngestRequest,
    user_id: str = Query(..., min_length=1),
) -> BulkIngestResponse:
    start = now_utc()
    successful, failed = await memory_aggregator.ingest_bulk(user_id, request.entries)
    processing_time_ms = int((now_utc() - start).total_seconds() * 1000)
    return BulkIngestResponse(
        successful=successful,
        failed=failed,
        total_processing_time_ms=processing_time_ms,
    )


@router.delete("/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory_entry(
    entry_id: str,
    user_id: str = Query(..., min_length=1),
) -> None:
    deleted = await factory.memory_store.delete(user_id, entry_id)
    await factory.vector_store.delete(user_id, entry_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Entry not found")


@router.post("/compact", response_model=dict)
async def compact_memory(
    user_id: str = Query(..., min_length=1),
    remove_stale: bool = Query(False),
    merge_duplicates: bool = Query(False),
) -> dict:
    decayed = await compounding_service.decay_stale_entries(user_id)
    removed = []
    if remove_stale:
        threshold = now_utc() - timedelta(days=90)
        records = await factory.memory_store.list_all(user_id)
        for record in records:
            last_accessed = record.last_accessed_at or record.indexed_at
            if last_accessed < threshold:
                await factory.memory_store.delete(user_id, record.id)
                await factory.vector_store.delete(user_id, record.id)
                removed.append(record.id)
    merged = []
    if merge_duplicates:
        merged = await compounding_service.merge_near_duplicates(user_id)
    new_links = await compounding_service.find_new_connections(user_id)
    return {
        "decayed": decayed,
        "removed": removed,
        "merged": merged,
        "new_connections": new_links,
    }
