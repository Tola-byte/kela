import pytest

from services.embedding import LocalVoyageClient
from services.memory_index import MemoryIndexService
from services.memory_store import MemoryStore
from services.vector_store import LocalVectorStore
from services.memory_compounding import MemoryCompoundingService
from services.memory_aggregator import MemoryAggregator
from services.voice_profile_service import VoiceProfileService
from models import IngestRequest


@pytest.mark.asyncio
async def test_compounding_updates_voice_profile(tmp_path):
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
            content_type="article",
            title="Brand Voice",
            content="We speak with clarity and optimism. Keep sentences crisp.",
            tags=["voice"],
        ),
    )

    profile = await voice.get_profile("user-1")
    assert profile is not None
    assert profile.sample_size == 1
    assert profile.confidence > 0.0


@pytest.mark.asyncio
async def test_decay_reduces_relevance(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    vector_store = LocalVectorStore()
    voice = VoiceProfileService()
    compounding = MemoryCompoundingService(store, vector_store, voice)
    embedding = LocalVoyageClient()
    indexer = MemoryIndexService(vector_store, embedding)
    aggregator = MemoryAggregator(store, indexer, compounding)

    response = await aggregator.ingest(
        "user-1",
        IngestRequest(
            content_type="text_snippet",
            title="Old note",
            content="Legacy positioning notes",
        ),
    )

    decayed = await compounding.decay_stale_entries("user-1", decay_after_days=0, decay_rate=0.5)
    record = await store.get("user-1", response.entry_id)
    assert decayed == 1
    assert record.relevance_decay < 1.0
