# Integration Contract

## Services
- Vector search: Qdrant-style client with `init_collection`, `upsert`, `search`, `delete`
- Embedding: Voyage-style client with `embed`, `embed_batch`, `embed_query`
- Voice profile: `analyze_content`, `update_profile`, `get_profile`

## Expected Flow
1. Ingestion -> embed -> upsert -> metadata write -> compounding update
2. Retrieval -> embed query -> search -> recency blend -> context assembly
