from __future__ import annotations

import time
from datetime import datetime, timedelta

from models import CompoundingEvent, CompoundingResult
from .memory_store import MemoryStore
from .vector_store import LocalVectorStore
from .voice_profile_service import VoiceProfileService
from .utils import now_utc


class MemoryCompoundingService:
    def __init__(
        self,
        store: MemoryStore,
        vector_store: LocalVectorStore,
        voice_profile: VoiceProfileService,
    ) -> None:
        self.store = store
        self.vector_store = vector_store
        self.voice_profile = voice_profile
        self.related_entries_cache: dict[str, list[str]] = {}

    async def on_content_added(
        self,
        user_id: str,
        entry_id: str,
        content: str,
        content_type: str,
    ) -> CompoundingResult:
        start = time.time()
        new_connections = await self._update_related_entries(user_id, entry_id)
        voice_updated = False
        confidence_delta = 0.0
        if content_type in {"document", "text_snippet", "article", "notion_page"}:
            profile_before = await self.voice_profile.get_profile(user_id)
            await self.voice_profile.update_profile(user_id, content)
            profile_after = await self.voice_profile.get_profile(user_id)
            voice_updated = True
            if profile_before and profile_after:
                confidence_delta = profile_after.confidence - profile_before.confidence
            elif profile_after:
                confidence_delta = profile_after.confidence
        await self.store.add_compounding_event(
            user_id,
            "content_added",
            {"entry_id": entry_id, "new_connections": new_connections},
        )
        return CompoundingResult(
            user_id=user_id,
            voice_profile_updated=voice_updated,
            new_connections_found=new_connections,
            stale_entries_decayed=0,
            confidence_delta=confidence_delta,
            processing_time_ms=int((time.time() - start) * 1000),
        )

    async def on_content_accessed(
        self,
        user_id: str,
        entry_id: str,
        access_context: str | None = None,
    ) -> None:
        await self.store.update_access(user_id, entry_id)
        await self.store.add_compounding_event(
            user_id,
            "content_accessed",
            {"entry_id": entry_id, "context": access_context},
        )

    async def decay_stale_entries(
        self,
        user_id: str,
        decay_after_days: int = 30,
        decay_rate: float = 0.95,
    ) -> int:
        records = await self.store.list_all(user_id)
        threshold = now_utc() - timedelta(days=decay_after_days)
        decayed = 0
        for record in records:
            last_accessed = record.last_accessed_at or record.indexed_at
            if last_accessed < threshold:
                new_decay = max(0.1, record.relevance_decay * decay_rate)
                await self.store.update_decay(user_id, record.id, new_decay)
                decayed += 1
        if decayed:
            await self.store.add_compounding_event(
                user_id,
                "decay",
                {"decayed": decayed, "decay_rate": decay_rate},
            )
        return decayed

    async def find_new_connections(self, user_id: str, similarity_threshold: float = 0.8) -> int:
        records = await self.store.list_all(user_id)
        new_links = 0
        for record in records:
            before = set(record.related_entries)
            after = set(await self._find_related(user_id, record.id, similarity_threshold))
            if after - before:
                await self.store.update_related_entries(user_id, record.id, list(after))
                new_links += len(after - before)
        if new_links:
            await self.store.add_compounding_event(
                user_id,
                "recluster",
                {"new_links": new_links},
            )
        return new_links

    async def merge_near_duplicates(
        self,
        user_id: str,
        similarity_threshold: float = 0.95,
    ) -> list[tuple[str, str]]:
        merged: list[tuple[str, str]] = []
        records = {r.id: r for r in await self.store.list_all(user_id)}
        vectors = {doc_id: vec for doc_id, vec, _ in await self.vector_store.get_all(user_id)}
        seen: set[str] = set()
        for entry_id, record in records.items():
            if entry_id in seen:
                continue
            query_vec = vectors.get(entry_id)
            if not query_vec:
                continue
            results = await self.vector_store.search(
                user_id=user_id,
                query_vector=query_vec,
                limit=10,
                threshold=similarity_threshold,
            )
            for result in results:
                if result.doc_id == entry_id or result.doc_id in seen:
                    continue
                newer = record
                older = records.get(result.doc_id)
                if not older:
                    continue
                if older.indexed_at > record.indexed_at:
                    newer, older = older, record
                merged_tags = list(dict.fromkeys(newer.tags + older.tags))
                await self.store.update_content_fields(user_id, newer.id, newer.title, newer.content_preview, merged_tags)
                await self.store.delete(user_id, older.id)
                await self.vector_store.delete(user_id, older.id)
                merged.append((newer.id, older.id))
                seen.add(older.id)
            seen.add(entry_id)
        if merged:
            await self.store.add_compounding_event(
                user_id,
                "merge_duplicates",
                {"merged": merged},
            )
        return merged

    async def get_compounding_history(self, user_id: str, limit: int = 100) -> list[CompoundingEvent]:
        rows = await self.store.get_compounding_events(user_id, limit)
        return [
            CompoundingEvent(
                user_id=row["user_id"],
                event_type=row["event_type"],
                timestamp=datetime.fromisoformat(row["timestamp"]),
                details=row["details"],
            )
            for row in rows
        ]

    async def _update_related_entries(self, user_id: str, entry_id: str) -> int:
        related = await self._find_related(user_id, entry_id, 0.8)
        await self.store.update_related_entries(user_id, entry_id, related)
        for other_id in related:
            other = await self.store.get(user_id, other_id)
            if other and entry_id not in other.related_entries:
                await self.store.update_related_entries(user_id, other_id, other.related_entries + [entry_id])
        self.related_entries_cache[entry_id] = related
        return len(related)

    async def _find_related(self, user_id: str, entry_id: str, threshold: float) -> list[str]:
        query_vec = await self.vector_store.get_vector(user_id, entry_id)
        if not query_vec:
            return []
        results = await self.vector_store.search(
            user_id=user_id,
            query_vector=query_vec,
            limit=10,
            threshold=threshold,
        )
        return [r.doc_id for r in results if r.doc_id != entry_id]
