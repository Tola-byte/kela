from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .utils import cosine_similarity


@dataclass
class SearchResult:
    doc_id: str
    score: float
    payload: dict[str, Any]


class LocalVectorStore:
    """Simple in-memory vector store to mimic Qdrant behavior."""

    def __init__(self) -> None:
        self.collections: dict[str, dict[str, tuple[list[float], dict[str, Any]]]] = {}

    async def init_collection(self, user_id: str) -> bool:
        name = f"user_{user_id}"
        if name not in self.collections:
            self.collections[name] = {}
        return True

    async def upsert(
        self,
        user_id: str,
        doc_id: str,
        vector: list[float],
        payload: dict[str, Any],
    ) -> bool:
        name = f"user_{user_id}"
        if name not in self.collections:
            await self.init_collection(user_id)
        self.collections[name][doc_id] = (vector, payload)
        return True

    async def search(
        self,
        user_id: str,
        query_vector: list[float],
        limit: int = 20,
        threshold: float = 0.5,
        type_filter: str | None = None,
    ) -> list[SearchResult]:
        name = f"user_{user_id}"
        if name not in self.collections:
            return []

        results: list[SearchResult] = []
        for doc_id, (vector, payload) in self.collections[name].items():
            if type_filter and payload.get("type") != type_filter:
                continue
            score = cosine_similarity(query_vector, vector)
            if score >= threshold:
                results.append(SearchResult(doc_id=doc_id, score=score, payload=payload))
        results.sort(key=lambda item: item.score, reverse=True)
        return results[:limit]

    async def delete(self, user_id: str, doc_id: str) -> bool:
        name = f"user_{user_id}"
        if name in self.collections and doc_id in self.collections[name]:
            del self.collections[name][doc_id]
            return True
        return False

    async def get_vector(self, user_id: str, doc_id: str) -> list[float] | None:
        name = f"user_{user_id}"
        if name not in self.collections or doc_id not in self.collections[name]:
            return None
        return self.collections[name][doc_id][0]

    async def get_all(self, user_id: str) -> list[tuple[str, list[float], dict[str, Any]]]:
        name = f"user_{user_id}"
        if name not in self.collections:
            return []
        return [(doc_id, vec, payload) for doc_id, (vec, payload) in self.collections[name].items()]
