from __future__ import annotations

from .factory import factory
from .memory_compounding import MemoryCompoundingService
from .memory_index import MemoryIndexService
from .memory_aggregator import MemoryAggregator
from .context_builder import ContextBuilder
from .memory_stats import MemoryStatsService


compounding_service = MemoryCompoundingService(
    store=factory.memory_store,
    vector_store=factory.vector_store,
    voice_profile=factory.voice_profile_service,
)

index_service = MemoryIndexService(
    vector_store=factory.vector_store,
    embedding_client=factory.embedding_client,
)

memory_aggregator = MemoryAggregator(
    store=factory.memory_store,
    indexer=index_service,
    compounding=compounding_service,
)

context_builder = ContextBuilder(
    store=factory.memory_store,
    vector_store=factory.vector_store,
    embedding_client=factory.embedding_client,
    voice_profile=factory.voice_profile_service,
)

memory_stats = MemoryStatsService(store=factory.memory_store)
