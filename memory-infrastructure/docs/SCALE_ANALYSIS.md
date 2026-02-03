# Scale Analysis

## 1K Users
- Single node FastAPI instance handles traffic.
- Qdrant collection per user is manageable.
- SQLite/InstantDB load is modest.

## 10K Users
- Move vector search to managed Qdrant Cloud.
- Add a shared cache for context retrieval (Redis).
- Move metadata to InstantDB with indexes on user_id and content_type.
- Introduce background worker pool for compounding jobs.

## 100K Users
- Shard Qdrant collections across clusters by user hash.
- Async ingestion pipeline with queue (Kafka/SQS) and dead-letter handling.
- Partition metadata storage by user_id and time.
- Precompute topic clusters and store summaries.

## Bottlenecks
- Embedding generation throughput
- Vector search latency at high dimensionality
- Metadata reads during context assembly

## Mitigations
- Batch embedding and caching
- ANN tuning + filtered search
- Materialized views for frequently accessed context
