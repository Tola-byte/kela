# Architecture

## Overview
The system is a memory infrastructure layer that ingests user content, generates embeddings, stores vectors, and provides contextual retrieval with compounding behaviors. The backend exposes FastAPI endpoints for memory and context APIs, and the frontend provides a debug dashboard to visualize memory health.

## Data Flow
1. **Ingest** (`POST /api/memory/ingest`)
   - Receive content payload
   - Generate embedding (Voyage adapter)
   - Upsert vector to Qdrant-style store
   - Persist metadata to MemoryStore (SQLite in local dev)
   - Trigger compounding (related entries + voice profile)

2. **Retrieve Context** (`POST /api/context/retrieve`)
   - Embed query
   - Semantic search
   - Rank by relevance (70%) + recency (30%)
   - Assemble context within token budget
   - Return sources + context text

3. **Compounding**
   - On ingest: discover related entries and update voice profile
   - On access: increment access + reset decay
   - Background: decay stale entries, find new connections, merge duplicates

## Storage
- **Vectors**: Local vector store (swap with Qdrant in production)
- **Metadata**: SQLite `MemoryStore` (swap with InstantDB in production)
- **Voice Profile**: In-memory profile service (swap with Claude-based service in production)

## Integration Points
- `vector_store.py` matches Qdrant client interface
- `embedding.py` matches Voyage client interface
- `voice_profile_service.py` mirrors voice profile service API

## Compounding Algorithm
- Related entries: similarity threshold 0.8
- Duplicate detection: similarity threshold 0.95
- Decay: 30 days idle, decay rate 0.95

## Observability
- Compounding events persisted in store for audit and dashboard.
