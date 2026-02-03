# Memory API Contract

Base path: `/api/memory`

- `GET /stats?user_id=` → MemoryStats
- `GET /health?user_id=` → MemoryHealthReport
- `GET /entries?user_id=&content_type=&limit=&offset=&sort_by=` → list[MemoryEntry]
- `GET /entries/{entry_id}?user_id=` → MemoryEntry
- `POST /ingest?user_id=` → IngestResponse
- `POST /ingest/bulk?user_id=` → BulkIngestResponse
- `DELETE /entries/{entry_id}?user_id=` → 204
- `POST /compact?user_id=&remove_stale=&merge_duplicates=` → maintenance response
