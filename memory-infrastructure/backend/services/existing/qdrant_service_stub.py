"""
Qdrant Service Stub - READ ONLY REFERENCE
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class SearchResult:
    doc_id: str
    score: float
    payload: dict[str, Any]


class QdrantService:
    """Per-user isolated vector collections."""

    async def init_collection(self, user_id: str) -> bool:
        raise NotImplementedError("Use mock in tests")

    async def upsert(
        self,
        user_id: str,
        doc_id: str,
        vector: list[float],
        payload: dict[str, Any],
    ) -> bool:
        raise NotImplementedError("Use mock in tests")

    async def search(
        self,
        user_id: str,
        query_vector: list[float],
        limit: int = 20,
        threshold: float = 0.5,
        type_filter: str | None = None,
    ) -> list[SearchResult]:
        raise NotImplementedError("Use mock in tests")

    async def delete(self, user_id: str, doc_id: str) -> bool:
        raise NotImplementedError("Use mock in tests")
