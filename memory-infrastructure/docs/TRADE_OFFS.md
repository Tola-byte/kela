# Trade-offs

## Local Adapters vs Production Clients
- **Choice**: Use local embedding/vector adapters for easy setup.
- **Trade-off**: Deterministic embeddings are not semantically meaningful but enable repeatable demos.

## SQLite Metadata Store
- **Choice**: SQLite for local metadata storage.
- **Trade-off**: Single-node storage; production should use InstantDB or Postgres.

## Simple Recency Scoring
- **Choice**: Exponential decay to blend recency.
- **Trade-off**: Easy to reason about but not as nuanced as user-specific recency models.

## Duplicate Merge Strategy
- **Choice**: Keep newer record, merge tags, delete older.
- **Trade-off**: Potential loss of metadata. In production, keep a merge trail.

## Next Steps (2 Weeks)
- Async ingestion queue + retry policies
- Real-time memory dashboard (InstantDB)
- Embedding versioning + reindexing workflow
- Cross-user anonymized insights with privacy guarantees
