from __future__ import annotations

from datetime import timedelta

from models import MemoryHealthReport, MemoryStats
from .memory_store import MemoryStore
from .utils import now_utc


class MemoryStatsService:
    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    async def get_stats(self, user_id: str, voice_confidence: float, last_compounding: str | None) -> MemoryStats:
        stats = await self.store.stats(user_id)
        health_score = self._health_score(stats["entries_by_type"], stats["total_entries"], stats["newest"])
        return MemoryStats(
            user_id=user_id,
            total_entries=stats["total_entries"],
            entries_by_type=stats["entries_by_type"],
            total_tokens_indexed=stats["total_tokens"],
            memory_health_score=health_score,
            oldest_entry=stats["oldest"],
            newest_entry=stats["newest"],
            voice_profile_confidence=voice_confidence,
            last_compounding_run=last_compounding,
        )

    async def get_health_report(
        self,
        user_id: str,
        voice_confidence: float,
        last_compounding: str | None,
    ) -> MemoryHealthReport:
        stats = await self.get_stats(user_id, voice_confidence, last_compounding)
        records = await self.store.list_all(user_id)
        stale_entries = []
        recommendations = []
        thirty_days_ago = now_utc() - timedelta(days=30)
        for record in records:
            last_accessed = record.last_accessed_at or record.indexed_at
            if last_accessed < thirty_days_ago:
                stale_entries.append(record.id)
        if len(stale_entries) > 5:
            recommendations.append("Consider pruning stale entries to keep memory fresh.")
        if stats.total_entries < 5:
            recommendations.append("Add more content to improve retrieval quality.")
        if len(stats.entries_by_type) < 2:
            recommendations.append("Diversity is low; add more content types.")
        return MemoryHealthReport(
            stats=stats,
            recommendations=recommendations,
            stale_entries=stale_entries,
            duplicate_candidates=[],
        )

    @staticmethod
    def _health_score(entries_by_type: dict[str, int], total_entries: int, newest_entry) -> float:
        if total_entries == 0:
            return 0.0
        diversity = min(len(entries_by_type) / 5.0, 1.0)
        recency = 1.0 if newest_entry else 0.5
        score = (0.6 * diversity + 0.4 * recency) * 100
        return round(score, 2)
