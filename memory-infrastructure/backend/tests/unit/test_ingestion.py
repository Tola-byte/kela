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
async def test_ingest_creates_entry(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    vector_store = LocalVectorStore()
    embedding = LocalVoyageClient()
    voice = VoiceProfileService()
    compounding = MemoryCompoundingService(store, vector_store, voice)
    indexer = MemoryIndexService(vector_store, embedding)
    aggregator = MemoryAggregator(store, indexer, compounding)

    request = IngestRequest(
        content_type="text_snippet",
        title="Test Note",
        content="This is a short memory snippet about growth.",
        source_url=None,
        metadata={"source": "unit"},
        tags=["growth"],
    )

    response = await aggregator.ingest("user-1", request)

    record = await store.get("user-1", response.entry_id)
    assert record is not None
    assert record.title == "Test Note"
    assert record.content_preview.startswith("This is a short")
    assert response.related_entries == []
