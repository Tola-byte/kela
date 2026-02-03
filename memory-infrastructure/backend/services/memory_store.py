from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import anyio

from .utils import now_utc


@dataclass
class MemoryRecord:
    id: str
    user_id: str
    content_type: str
    title: str
    content_preview: str
    content: str
    embedding_id: str
    indexed_at: datetime
    last_accessed_at: datetime | None
    access_count: int
    relevance_decay: float
    source_url: str | None
    source_metadata: dict | None
    related_entries: list[str]
    tags: list[str]
    token_count: int


class MemoryStore:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = self._connect()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memory_entries (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content_preview TEXT NOT NULL,
                    content TEXT NOT NULL,
                    embedding_id TEXT NOT NULL,
                    indexed_at TEXT NOT NULL,
                    last_accessed_at TEXT,
                    access_count INTEGER NOT NULL,
                    relevance_decay REAL NOT NULL,
                    source_url TEXT,
                    source_metadata TEXT,
                    related_entries TEXT,
                    tags TEXT,
                    token_count INTEGER NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS compounding_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    details TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_memory_user ON memory_entries(user_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_memory_user_type ON memory_entries(user_id, content_type)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_memory_indexed_at ON memory_entries(indexed_at)"
            )
            conn.commit()
        finally:
            conn.close()

    async def upsert(self, record: MemoryRecord) -> None:
        await anyio.to_thread.run_sync(self._upsert_sync, record)

    def _upsert_sync(self, record: MemoryRecord) -> None:
        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT INTO memory_entries (
                    id, user_id, content_type, title, content_preview, content, embedding_id,
                    indexed_at, last_accessed_at, access_count, relevance_decay, source_url,
                    source_metadata, related_entries, tags, token_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title=excluded.title,
                    content_preview=excluded.content_preview,
                    content=excluded.content,
                    embedding_id=excluded.embedding_id,
                    indexed_at=excluded.indexed_at,
                    last_accessed_at=excluded.last_accessed_at,
                    access_count=excluded.access_count,
                    relevance_decay=excluded.relevance_decay,
                    source_url=excluded.source_url,
                    source_metadata=excluded.source_metadata,
                    related_entries=excluded.related_entries,
                    tags=excluded.tags,
                    token_count=excluded.token_count
                """,
                (
                    record.id,
                    record.user_id,
                    record.content_type,
                    record.title,
                    record.content_preview,
                    record.content,
                    record.embedding_id,
                    record.indexed_at.isoformat(),
                    record.last_accessed_at.isoformat() if record.last_accessed_at else None,
                    record.access_count,
                    record.relevance_decay,
                    record.source_url,
                    json.dumps(record.source_metadata) if record.source_metadata else None,
                    json.dumps(record.related_entries),
                    json.dumps(record.tags),
                    record.token_count,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    async def get(self, user_id: str, entry_id: str) -> MemoryRecord | None:
        return await anyio.to_thread.run_sync(self._get_sync, user_id, entry_id)

    def _get_sync(self, user_id: str, entry_id: str) -> MemoryRecord | None:
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT * FROM memory_entries WHERE user_id = ? AND id = ?",
                (user_id, entry_id),
            ).fetchone()
            return self._row_to_record(row) if row else None
        finally:
            conn.close()

    async def list(
        self,
        user_id: str,
        content_type: str | None,
        limit: int,
        offset: int,
        sort_by: str,
    ) -> list[MemoryRecord]:
        return await anyio.to_thread.run_sync(
            self._list_sync, user_id, content_type, limit, offset, sort_by
        )

    def _list_sync(
        self,
        user_id: str,
        content_type: str | None,
        limit: int,
        offset: int,
        sort_by: str,
    ) -> list[MemoryRecord]:
        conn = self._connect()
        try:
            if sort_by not in {"indexed_at", "last_accessed_at", "relevance_decay"}:
                sort_by = "indexed_at"
            query = "SELECT * FROM memory_entries WHERE user_id = ?"
            params: list[Any] = [user_id]
            if content_type:
                query += " AND content_type = ?"
                params.append(content_type)
            query += f" ORDER BY {sort_by} DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            rows = conn.execute(query, tuple(params)).fetchall()
            return [self._row_to_record(row) for row in rows]
        finally:
            conn.close()

    async def delete(self, user_id: str, entry_id: str) -> bool:
        return await anyio.to_thread.run_sync(self._delete_sync, user_id, entry_id)

    def _delete_sync(self, user_id: str, entry_id: str) -> bool:
        conn = self._connect()
        try:
            cur = conn.execute(
                "DELETE FROM memory_entries WHERE user_id = ? AND id = ?",
                (user_id, entry_id),
            )
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()

    async def update_access(
        self,
        user_id: str,
        entry_id: str,
        accessed_at: datetime | None = None,
        increment: int = 1,
        reset_decay: bool = True,
    ) -> None:
        await anyio.to_thread.run_sync(
            self._update_access_sync, user_id, entry_id, accessed_at, increment, reset_decay
        )

    def _update_access_sync(
        self,
        user_id: str,
        entry_id: str,
        accessed_at: datetime | None,
        increment: int,
        reset_decay: bool,
    ) -> None:
        accessed_at = accessed_at or now_utc()
        conn = self._connect()
        try:
            decay_stmt = "relevance_decay = 1.0" if reset_decay else "relevance_decay = relevance_decay"
            conn.execute(
                f"""
                UPDATE memory_entries
                SET last_accessed_at = ?,
                    access_count = access_count + ?,
                    {decay_stmt}
                WHERE user_id = ? AND id = ?
                """,
                (accessed_at.isoformat(), increment, user_id, entry_id),
            )
            conn.commit()
        finally:
            conn.close()

    async def update_related_entries(self, user_id: str, entry_id: str, related_entries: list[str]) -> None:
        await anyio.to_thread.run_sync(self._update_related_entries_sync, user_id, entry_id, related_entries)

    def _update_related_entries_sync(self, user_id: str, entry_id: str, related_entries: list[str]) -> None:
        conn = self._connect()
        try:
            conn.execute(
                "UPDATE memory_entries SET related_entries = ? WHERE user_id = ? AND id = ?",
                (json.dumps(related_entries), user_id, entry_id),
            )
            conn.commit()
        finally:
            conn.close()

    async def update_decay(self, user_id: str, entry_id: str, new_decay: float) -> None:
        await anyio.to_thread.run_sync(self._update_decay_sync, user_id, entry_id, new_decay)

    def _update_decay_sync(self, user_id: str, entry_id: str, new_decay: float) -> None:
        conn = self._connect()
        try:
            conn.execute(
                "UPDATE memory_entries SET relevance_decay = ? WHERE user_id = ? AND id = ?",
                (new_decay, user_id, entry_id),
            )
            conn.commit()
        finally:
            conn.close()

    async def update_content_fields(
        self, user_id: str, entry_id: str, title: str, preview: str, tags: list[str]
    ) -> None:
        await anyio.to_thread.run_sync(self._update_content_fields_sync, user_id, entry_id, title, preview, tags)

    def _update_content_fields_sync(
        self, user_id: str, entry_id: str, title: str, preview: str, tags: list[str]
    ) -> None:
        conn = self._connect()
        try:
            conn.execute(
                "UPDATE memory_entries SET title = ?, content_preview = ?, tags = ? WHERE user_id = ? AND id = ?",
                (title, preview, json.dumps(tags), user_id, entry_id),
            )
            conn.commit()
        finally:
            conn.close()

    async def list_all(self, user_id: str) -> list[MemoryRecord]:
        return await anyio.to_thread.run_sync(self._list_all_sync, user_id)

    def _list_all_sync(self, user_id: str) -> list[MemoryRecord]:
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT * FROM memory_entries WHERE user_id = ?",
                (user_id,),
            ).fetchall()
            return [self._row_to_record(row) for row in rows]
        finally:
            conn.close()

    async def add_compounding_event(self, user_id: str, event_type: str, details: dict) -> None:
        await anyio.to_thread.run_sync(self._add_compounding_event_sync, user_id, event_type, details)

    def _add_compounding_event_sync(self, user_id: str, event_type: str, details: dict) -> None:
        conn = self._connect()
        try:
            conn.execute(
                "INSERT INTO compounding_events (user_id, event_type, timestamp, details) VALUES (?, ?, ?, ?)",
                (user_id, event_type, now_utc().isoformat(), json.dumps(details)),
            )
            conn.commit()
        finally:
            conn.close()

    async def get_compounding_events(self, user_id: str, limit: int) -> list[dict]:
        return await anyio.to_thread.run_sync(self._get_compounding_events_sync, user_id, limit)

    def _get_compounding_events_sync(self, user_id: str, limit: int) -> list[dict]:
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT user_id, event_type, timestamp, details FROM compounding_events WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
                (user_id, limit),
            ).fetchall()
            return [
                {
                    "user_id": row["user_id"],
                    "event_type": row["event_type"],
                    "timestamp": row["timestamp"],
                    "details": json.loads(row["details"]),
                }
                for row in rows
            ]
        finally:
            conn.close()

    async def stats(self, user_id: str) -> dict:
        return await anyio.to_thread.run_sync(self._stats_sync, user_id)

    def _stats_sync(self, user_id: str) -> dict:
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT content_type, COUNT(*) AS count, SUM(token_count) AS tokens, MIN(indexed_at) AS oldest, MAX(indexed_at) AS newest FROM memory_entries WHERE user_id = ? GROUP BY content_type",
                (user_id,),
            ).fetchall()
            total_entries = 0
            total_tokens = 0
            entries_by_type: dict[str, int] = {}
            oldest = None
            newest = None
            for row in rows:
                count = row["count"] or 0
                tokens = row["tokens"] or 0
                total_entries += count
                total_tokens += tokens
                entries_by_type[row["content_type"]] = count
                if row["oldest"]:
                    ts = datetime.fromisoformat(row["oldest"])
                    oldest = ts if not oldest or ts < oldest else oldest
                if row["newest"]:
                    ts = datetime.fromisoformat(row["newest"])
                    newest = ts if not newest or ts > newest else newest
            return {
                "total_entries": total_entries,
                "total_tokens": total_tokens,
                "entries_by_type": entries_by_type,
                "oldest": oldest,
                "newest": newest,
            }
        finally:
            conn.close()

    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> MemoryRecord:
        return MemoryRecord(
            id=row["id"],
            user_id=row["user_id"],
            content_type=row["content_type"],
            title=row["title"],
            content_preview=row["content_preview"],
            content=row["content"],
            embedding_id=row["embedding_id"],
            indexed_at=datetime.fromisoformat(row["indexed_at"]),
            last_accessed_at=datetime.fromisoformat(row["last_accessed_at"]) if row["last_accessed_at"] else None,
            access_count=row["access_count"],
            relevance_decay=row["relevance_decay"],
            source_url=row["source_url"],
            source_metadata=json.loads(row["source_metadata"]) if row["source_metadata"] else None,
            related_entries=json.loads(row["related_entries"] or "[]"),
            tags=json.loads(row["tags"] or "[]"),
            token_count=row["token_count"],
        )
