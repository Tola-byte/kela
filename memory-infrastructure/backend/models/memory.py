from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ContentType = Literal[
    "document",
    "video",
    "audio",
    "link",
    "text_snippet",
    "youtube_video",
    "instagram_post",
    "notion_page",
    "article",
]


class MemoryEntry(BaseModel):
    id: str
    user_id: str
    content_type: ContentType
    title: str
    content_preview: str = Field(..., max_length=500)
    embedding_id: str
    indexed_at: datetime
    last_accessed_at: datetime | None = None
    access_count: int = 0
    relevance_decay: float = 1.0
    source_url: str | None = None
    source_metadata: dict | None = None
    related_entries: list[str] = []
    tags: list[str] = []


class MemoryStats(BaseModel):
    user_id: str
    total_entries: int
    entries_by_type: dict[str, int]
    total_tokens_indexed: int
    memory_health_score: float
    oldest_entry: datetime | None
    newest_entry: datetime | None
    voice_profile_confidence: float
    last_compounding_run: datetime | None


class MemoryHealthReport(BaseModel):
    stats: MemoryStats
    recommendations: list[str]
    stale_entries: list[str]
    duplicate_candidates: list[tuple[str, str, float]]


class IngestRequest(BaseModel):
    content_type: ContentType
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1, max_length=100000)
    source_url: str | None = None
    metadata: dict | None = None
    tags: list[str] = []


class IngestResponse(BaseModel):
    entry_id: str
    indexed: bool
    embedding_id: str
    token_count: int
    related_entries: list[str]
    processing_time_ms: int


class BulkIngestRequest(BaseModel):
    entries: list[IngestRequest] = Field(..., max_length=50)


class BulkIngestResponse(BaseModel):
    successful: list[IngestResponse]
    failed: list[dict]
    total_processing_time_ms: int


class ContextSource(BaseModel):
    entry_id: str
    title: str
    content_type: str
    relevance_score: float
    excerpt: str = Field(..., max_length=500)
    source_url: str | None = None


class RetrievedContext(BaseModel):
    query: str
    sources: list[ContextSource]
    context_text: str
    token_count: int
    voice_summary: str | None = None
    retrieval_time_ms: int
    sources_considered: int
    sources_included: int


class ContextRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    max_tokens: int = Field(2000, ge=100, le=8000)
    max_sources: int = Field(5, ge=1, le=20)
    content_types: list[str] | None = None
    recency_days: int | None = None
    min_relevance: float = Field(0.5, ge=0.0, le=1.0)
    include_voice_profile: bool = True
    include_source_metadata: bool = True
    format: Literal["markdown", "plain", "xml"] = "markdown"


class VoiceContextRequest(BaseModel):
    sample_text: str | None = None
    include_examples: bool = True
    max_examples: int = Field(3, ge=1, le=10)


class VoiceContext(BaseModel):
    profile_summary: str
    tone_guidance: str
    vocabulary_hints: list[str]
    phrases_to_use: list[str]
    things_to_avoid: list[str]
    example_excerpts: list[str]
    confidence: float


class CompoundingEvent(BaseModel):
    user_id: str
    event_type: str
    timestamp: datetime
    details: dict


class CompoundingResult(BaseModel):
    user_id: str
    voice_profile_updated: bool
    new_connections_found: int
    stale_entries_decayed: int
    confidence_delta: float
    processing_time_ms: int
