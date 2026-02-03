import pytest

from services.embedding import LocalVoyageClient
from services.memory_index import MemoryIndexService
from services.memory_store import MemoryStore
from services.vector_store import LocalVectorStore
from services.memory_compounding import MemoryCompoundingService
from services.memory_aggregator import MemoryAggregator
from services.context_builder import ContextBuilder
from services.voice_profile_service import VoiceProfileService
from models import IngestRequest, ContextRequest


@pytest.mark.asyncio
async def test_retrieve_context_returns_sources(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    vector_store = LocalVectorStore()
    embedding = LocalVoyageClient()
    voice = VoiceProfileService()
    compounding = MemoryCompoundingService(store, vector_store, voice)
    indexer = MemoryIndexService(vector_store, embedding)
    aggregator = MemoryAggregator(store, indexer, compounding)

    await aggregator.ingest(
        "user-1",
        IngestRequest(
            content_type="document",
            title="Marketing Playbook",
            content="This document covers retention, positioning, and storytelling.",
            tags=["marketing"],
        ),
    )

    builder = ContextBuilder(store, vector_store, embedding, voice)
    result = await builder.retrieve_context(
        "user-1",
        ContextRequest(query="How do I improve positioning?", max_tokens=500, max_sources=3),
    )

    assert result.sources
    assert result.sources[0].title == "Marketing Playbook"
    assert result.token_count > 0
